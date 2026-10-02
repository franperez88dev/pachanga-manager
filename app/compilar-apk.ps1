<#
  Compila el APK de PRUEBAS (debug) y, si se pide, lo instala en el móvil conectado por USB.

  Uso (en una terminal de VS Code, dentro de la carpeta "app"):
    .\compilar-apk.ps1                 # solo compila
    .\compilar-apk.ps1 -ComprobarMovil # no compila: dice si el móvil y el backend están listos
    .\compilar-apk.ps1 -Instalar       # compila, instala en el móvil y conecta con el backend del PC
    .\compilar-apk.ps1 -SoloConectar   # no compila: solo vuelve a conectar el móvil con el backend

  Pasos que hace (los mismos que harías a mano):
    1. Busca un JDK 17-24 (Gradle 8.14 no funciona con Java 25) y el SDK de Android.
    2. npm run build:movil       -> compila la web con la URL del backend para el móvil (.env.movil)
    3. npx cap sync android      -> copia esa web dentro del proyecto Android
    4. gradlew assembleDebug     -> genera el APK firmado con nuestro keystore
    5. (-Instalar) adb install -r -> lo instala en el móvil (encima de la versión anterior)
       adb reverse tcp:5000 tcp:5000 -> el 127.0.0.1:5000 del móvil pasa a ser el backend del PC
#>
param([switch]$Instalar, [switch]$SoloConectar, [switch]$ComprobarMovil)
# "Continue" y no "Stop": Gradle y npm escriben avisos por la salida de errores y PowerShell 5.1
# los tomaría por fallos. Si un paso falla de verdad, lo detectamos con $LASTEXITCODE.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot  # la carpeta "app", esté donde esté la terminal

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Green }
function Fallo($texto) { Write-Host "`nERROR: $texto" -ForegroundColor Red; exit 1 }

# --- SDK de Android y adb --------------------------------------------------------------
$sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "$env:LOCALAPPDATA\Android\Sdk" }
$adb = "$sdk\platform-tools\adb.exe"

# Pregunta a adb por el móvil y devuelve: "listo", "sin-permiso", "desconectado" o "ninguno"
function Estado-Movil {
  if (-not (Test-Path $adb)) { Fallo "No encuentro adb en $adb. Instala 'Android SDK Platform-Tools' desde el SDK Manager de Android Studio." }
  & $adb start-server *> $null
  $lineas = & $adb devices | Select-Object -Skip 1 | Where-Object { $_.Trim() }
  if ($lineas -match "`tdevice$") { return "listo" }
  if ($lineas -match "`tunauthorized$") { return "sin-permiso" }
  if ($lineas -match "`toffline$") { return "desconectado" }
  return "ninguno"
}

function Explicar-Movil($estado) {
  switch ($estado) {
    "listo" { Write-Host "OK  Móvil conectado y con la depuración USB autorizada." -ForegroundColor Green }
    "sin-permiso" { Write-Host "NO  El móvil está conectado, pero falta AUTORIZAR este PC: desbloquea el móvil y, en el aviso '¿Permitir depuración USB?', marca 'Permitir siempre' y pulsa 'Permitir'. Si no ves el aviso, desenchufa y vuelve a enchufar el cable." -ForegroundColor Yellow }
    "desconectado" { Write-Host "NO  El móvil aparece pero no responde: desenchufa el cable, espera 5 segundos y vuelve a enchufarlo." -ForegroundColor Yellow }
    default { Write-Host "NO  No se detecta ningún móvil en modo depuración. Revisa: 1) cable USB de datos bien enchufado, 2) 'Depuración USB' activada en Ajustes > Opciones de desarrollador, 3) móvil desbloqueado. (README, apartado 6.2)" -ForegroundColor Yellow }
  }
}

function Backend-Encendido {
  try { Invoke-RestMethod "http://127.0.0.1:5000/health" -TimeoutSec 3 | Out-Null; return $true } catch { return $false }
}

function Conectar-Movil {
  $estado = Estado-Movil
  if ($estado -ne "listo") { Explicar-Movil $estado; Fallo "El móvil no está listo (mira el mensaje de arriba)." }
  & $adb reverse tcp:5000 tcp:5000 | Out-Null
  Write-Host "Móvil conectado: su 127.0.0.1:5000 apunta ahora al backend de este PC."
  if (-not (Backend-Encendido)) {
    Write-Host "OJO: el backend NO está encendido. En otra terminal (carpeta backend): flask run --debug" -ForegroundColor Yellow
  }
}

if ($ComprobarMovil) {
  Paso "Comprobando el móvil"
  Explicar-Movil (Estado-Movil)
  Paso "Comprobando el backend (http://127.0.0.1:5000/health)"
  if (Backend-Encendido) { Write-Host "OK  El backend está encendido." -ForegroundColor Green }
  else { Write-Host "NO  El backend está apagado. En otra terminal, carpeta backend: .\.venv\Scripts\Activate.ps1 y luego flask run --debug" -ForegroundColor Yellow }
  exit 0
}

if ($SoloConectar) { Paso "Conectando el móvil con el backend"; Conectar-Movil; exit 0 }

# --- 1. JDK válido (17 a 24) -------------------------------------------------------------
Paso "Buscando el JDK y el SDK"
function Version-Java($carpeta) {
  $java = Join-Path $carpeta "bin\java.exe"
  if (-not (Test-Path $java)) { return 0 }
  $texto = (& cmd /c "`"$java`" -version 2>&1") -join " "
  if ($texto -match 'version "(\d+)') { return [int]$Matches[1] }
  return 0
}
$candidatos = @()
if ($env:JAVA_HOME) { $candidatos += $env:JAVA_HOME }
$candidatos += Get-ChildItem "$env:USERPROFILE\.jdks" -Directory -ErrorAction SilentlyContinue | ForEach-Object FullName
$candidatos += "F:\Android Studio\jbr", "C:\Program Files\Android\Android Studio\jbr"
$jdk = $candidatos | Where-Object { $v = Version-Java $_; $v -ge 17 -and $v -le 24 } | Select-Object -First 1
if (-not $jdk) {
  Fallo "No encuentro un JDK entre la versión 17 y la 24. Descarga el JDK 21 desde Android Studio (README, apartado 'Fase 3')."
}
$env:JAVA_HOME = $jdk
$env:ANDROID_HOME = $sdk
Write-Host "JDK: $jdk (Java $(Version-Java $jdk))"
Write-Host "SDK: $sdk"
if (-not (Test-Path "$sdk\platforms\android-36")) {
  Fallo "Falta la plataforma Android 36 en el SDK. Instálala desde el SDK Manager de Android Studio (README, apartado 'Fase 3')."
}

# --- 2 y 3. Web para el móvil y copia al proyecto Android ------------------------------
Paso "Compilando la web para el móvil (npm run build:movil)"
npm run build:movil
if ($LASTEXITCODE) { Fallo "Falló la compilación de la web." }

Paso "Copiando la web al proyecto Android (npx cap sync android)"
npx cap sync android
if ($LASTEXITCODE) { Fallo "Falló 'cap sync'." }

# --- 4. APK ------------------------------------------------------------------------------
Paso "Generando el APK de pruebas (gradlew assembleDebug). La primera vez tarda varios minutos."
Push-Location android
try {
  .\gradlew.bat assembleDebug
  if ($LASTEXITCODE) { Fallo "Falló Gradle. Lee el error de arriba." }
} finally { Pop-Location }

$apk = Resolve-Path "android\app\build\outputs\apk\debug\app-debug.apk"
$version = (Get-Content package.json -Raw | ConvertFrom-Json).version
Write-Host "`nAPK listo (versión $version): $apk" -ForegroundColor Cyan

# --- 5. Instalar en el móvil ----------------------------------------------------------
if ($Instalar) {
  Paso "Instalando en el móvil (adb install -r)"
  Conectar-Movil
  & $adb install -r $apk
  if ($LASTEXITCODE) { Fallo "No se pudo instalar. Si dice INSTALL_FAILED_UPDATE_INCOMPATIBLE, desinstala la app del móvil una vez." }
  Write-Host "`nInstalada. Abre 'Pachanga Manager' en el móvil." -ForegroundColor Cyan
}

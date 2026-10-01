// Dibujos de los avatares en SVG (un cuadrado de 100x100; el círculo lo pone el CSS).
// En JSX los atributos de SVG van en camelCase: stroke-width -> strokeWidth.

export function oscurecer(hex, factor) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 255, n & 255].map((v) => Math.round(v * (1 - factor)));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

const PELO = {
  calvo: () => <ellipse cx="43" cy="31" rx="6" ry="2.6" fill="#fff" opacity=".35" />,
  corto: (p) => <path d="M30,47 C27,26 39,20 50,20 C61,20 73,26 70,47 C68,39 66,34 62,31 C56,34 44,34 38,31 C34,34 32,39 30,47 Z" fill={p} />,
  tupe: (p) => <path d="M30,47 C27,29 34,21 44,19 C47,11 62,9 66,18 C71,22 73,31 70,47 C68,39 66,34 62,31 C56,34 44,34 38,31 C34,34 32,39 30,47 Z" fill={p} />,
  rizos: (p) => (
    <>
      {[[33, 40], [36, 31], [43, 25], [51, 23], [59, 25], [65, 31], [68, 40], [30, 48], [70, 48], [47, 30], [55, 30]]
        .map(([x, y]) => <circle key={`${x}-${y}`} cx={x} cy={y} r="7" fill={p} />)}
    </>
  ),
  melena: (p) => <path d="M28,52 C25,26 39,19 50,19 C61,19 75,26 72,52 C70,41 66,34 60,30 C53,36 42,36 37,31 C33,36 30,43 28,52 Z" fill={p} />,
  cresta: (p) => (
    <>
      <path d="M31,45 C30,30 40,25 50,25 C60,25 70,30 69,45 C66,37 60,34 50,34 C40,34 34,37 31,45 Z" fill={p} opacity=".35" />
      <path d="M44,35 L41,22 L47,26 L47,13 L52,23 L55,11 L56,24 L61,19 L57,35 Z" fill={p} />
    </>
  ),
};

const Bigote = ({ c }) => <path d="M40,57.5 Q45,53.5 50,55.5 Q55,53.5 60,57.5 Q55,60 50,58.3 Q45,60 40,57.5 Z" fill={c} />;
const MANDIBULA = "M31,47 C31,64 38,75 50,76 C62,75 69,64 69,47 C66,54 63,57 57,57 L43,57 C37,57 34,54 31,47 Z";
const BARBA = {
  ninguna: () => null,
  bigote: (c) => <Bigote c={c} />,
  perilla: (c) => (
    <>
      <Bigote c={c} />
      <path d="M44,64 Q50,62 56,64 Q55,72.5 50,73.5 Q45,72.5 44,64 Z" fill={c} />
    </>
  ),
  completa: (c) => (
    <>
      <path d={MANDIBULA} fill={c} />
      <Bigote c={c} />
    </>
  ),
};

export function Persona({ a, camiseta }) {
  const sombra = oscurecer(a.piel, 0.18);
  const conHueco = a.barba === "completa" || a.barba === "perilla"; // para que la boca se vea sobre la barba
  return (
    <>
      <rect width="100" height="100" fill="#cfe3d6" />
      {a.peinado === "melena" && <path d="M27,44 C24,66 27,84 33,96 L67,96 C73,84 76,66 73,44 Z" fill={a.color_pelo} />}
      <path d="M12,100 Q14,80 36,76 L64,76 Q86,80 88,100 Z" fill={camiseta} />
      <path d="M42,76 L50,84 L58,76" fill="none" stroke={oscurecer(camiseta, 0.25)} strokeWidth="2" />
      <rect x="43" y="62" width="14" height="16" rx="5" fill={sombra} />
      <circle cx="31" cy="49" r="5" fill={a.piel} />
      <circle cx="69" cy="49" r="5" fill={a.piel} />
      <ellipse cx="50" cy="47" rx="19" ry="22" fill={a.piel} />
      {(PELO[a.peinado] ?? PELO.corto)(a.color_pelo)}
      <path d="M38,40.5 h8 M54,40.5 h8" stroke={a.peinado === "calvo" ? sombra : a.color_pelo} strokeWidth="2.4" strokeLinecap="round" />
      <circle cx="42" cy="47" r="2.4" fill="#1d1d1d" />
      <circle cx="58" cy="47" r="2.4" fill="#1d1d1d" />
      <circle cx="42.8" cy="46.2" r=".8" fill="#fff" />
      <circle cx="58.8" cy="46.2" r=".8" fill="#fff" />
      <path d="M50,49 q-3,5.5 0,6.5" stroke={sombra} strokeWidth="1.6" fill="none" strokeLinecap="round" />
      {(BARBA[a.barba] ?? BARBA.ninguna)(a.color_barba)}
      {conHueco && <ellipse cx="50" cy="61" rx="7.5" ry="3.2" fill={a.piel} />}
      <path d="M44,60.5 q6,4.5 12,0" stroke="#7a3b2e" strokeWidth="2" fill="none" strokeLinecap="round" />
    </>
  );
}

export const ESPECIALES = {
  alien: () => (
    <>
      <rect width="100" height="100" fill="#1b1f3b" />
      <circle cx="15" cy="18" r="1.2" fill="#fff" /><circle cx="84" cy="26" r="1" fill="#fff" />
      <circle cx="76" cy="84" r="1.3" fill="#fff" /><circle cx="20" cy="78" r="1" fill="#fff" />
      <path d="M43,24 L36,9 M57,24 L64,9" stroke="#7ed957" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="36" cy="9" r="3.5" fill="#f5e663" /><circle cx="64" cy="9" r="3.5" fill="#f5e663" />
      <path d="M50,20 C74,20 80,40 73,57 C67,73 57,82 50,82 C43,82 33,73 27,57 C20,40 26,20 50,20 Z" fill="#7ed957" />
      <ellipse cx="39" cy="50" rx="7.5" ry="12" transform="rotate(28 39 50)" fill="#111" />
      <ellipse cx="61" cy="50" rx="7.5" ry="12" transform="rotate(-28 61 50)" fill="#111" />
      <circle cx="37" cy="45" r="2" fill="#fff" /><circle cx="59" cy="45" r="2" fill="#fff" />
      <path d="M45,70 q5,3 10,0" stroke="#2d6b18" strokeWidth="2" fill="none" strokeLinecap="round" />
    </>
  ),
  perro: () => (
    <>
      <rect width="100" height="100" fill="#ffe6b3" />
      <ellipse cx="25" cy="50" rx="10" ry="22" transform="rotate(18 25 50)" fill="#6b3e1f" />
      <ellipse cx="75" cy="50" rx="10" ry="22" transform="rotate(-18 75 50)" fill="#6b3e1f" />
      <ellipse cx="50" cy="50" rx="25" ry="27" fill="#c98b4f" />
      <ellipse cx="60" cy="42" rx="9" ry="8" fill="#8a5428" />
      <ellipse cx="50" cy="64" rx="15" ry="12" fill="#f0d2a8" />
      <circle cx="41" cy="44" r="3" fill="#1d1d1d" /><circle cx="60" cy="43" r="3" fill="#1d1d1d" />
      <circle cx="42" cy="43" r="1" fill="#fff" /><circle cx="61" cy="42" r="1" fill="#fff" />
      <ellipse cx="50" cy="58" rx="5.5" ry="4" fill="#1d1d1d" />
      <path d="M50,62 L50,66 M43,66 q7,5 14,0" stroke="#1d1d1d" strokeWidth="1.8" fill="none" strokeLinecap="round" />
      <path d="M47,68 q3,9 6,0 Z" fill="#ef6f8a" />
    </>
  ),
  gato: () => (
    <>
      <rect width="100" height="100" fill="#d9ecff" />
      <path d="M27,40 L30,14 L47,30 Z M73,40 L70,14 L53,30 Z" fill="#8f8f8f" />
      <path d="M31,34 L32,20 L42,29 Z M69,34 L68,20 L58,29 Z" fill="#f4a6b7" />
      <ellipse cx="50" cy="54" rx="26" ry="24" fill="#a6a6a6" />
      <path d="M44,32 L46,40 M50,31 L50,40 M56,32 L54,40" stroke="#7b7b7b" strokeWidth="2" strokeLinecap="round" />
      <ellipse cx="40" cy="51" rx="5" ry="6" fill="#9be15d" /><ellipse cx="60" cy="51" rx="5" ry="6" fill="#9be15d" />
      <ellipse cx="40" cy="51" rx="1.6" ry="5" fill="#111" /><ellipse cx="60" cy="51" rx="1.6" ry="5" fill="#111" />
      <path d="M47,60 L53,60 L50,63.5 Z" fill="#f4a6b7" />
      <path d="M50,63.5 q-3,4 -6,1 M50,63.5 q3,4 6,1" stroke="#333" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <path d="M36,61 L20,58 M36,64 L21,66 M64,61 L80,58 M64,64 L79,66" stroke="#555" strokeWidth="1" strokeLinecap="round" />
    </>
  ),
  pepino: () => (
    <>
      <rect width="100" height="100" fill="#fff5d6" />
      <path d="M48,14 q4,-6 8,-3" stroke="#6b4b1d" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      <rect x="31" y="14" width="38" height="78" rx="19" fill="#4c9a2a" />
      <path d="M40,22 L40,84 M50,18 L50,88 M60,22 L60,84" stroke="#6fbf45" strokeWidth="3" opacity=".55" strokeLinecap="round" />
      <circle cx="37" cy="30" r="1.6" fill="#2f6b17" /><circle cx="63" cy="36" r="1.6" fill="#2f6b17" />
      <circle cx="36" cy="72" r="1.6" fill="#2f6b17" /><circle cx="64" cy="78" r="1.6" fill="#2f6b17" />
      <circle cx="43" cy="46" r="4" fill="#fff" /><circle cx="57" cy="46" r="4" fill="#fff" />
      <circle cx="44" cy="47" r="2" fill="#1d1d1d" /><circle cx="58" cy="47" r="2" fill="#1d1d1d" />
      <path d="M43,57 q7,6 14,0" stroke="#1d1d1d" strokeWidth="2" fill="none" strokeLinecap="round" />
      <ellipse cx="38" cy="54" rx="3" ry="1.8" fill="#f28b8b" opacity=".6" />
      <ellipse cx="62" cy="54" rx="3" ry="1.8" fill="#f28b8b" opacity=".6" />
    </>
  ),
  calabaza: () => (
    <>
      <rect width="100" height="100" fill="#2b1d3a" />
      <path d="M50,24 q-2,-9 5,-12" stroke="#3f7a2a" strokeWidth="4" fill="none" strokeLinecap="round" />
      <ellipse cx="32" cy="57" rx="16" ry="27" fill="#e2761b" /><ellipse cx="68" cy="57" rx="16" ry="27" fill="#e2761b" />
      <ellipse cx="50" cy="57" rx="20" ry="30" fill="#f28c28" />
      <path d="M40,30 q-5,27 0,54 M60,30 q5,27 0,54" stroke="#c9631a" strokeWidth="1.5" fill="none" />
      <path d="M36,50 L42,42 L47,50 Z M53,50 L58,42 L64,50 Z" fill="#ffd34d" />
      <path d="M47,58 L50,54 L53,58 Z" fill="#ffd34d" />
      <path d="M33,64 L38,68 L43,64 L48,69 L53,64 L58,69 L63,64 L67,64 Q60,78 50,78 Q40,78 33,64 Z" fill="#ffd34d" />
    </>
  ),
};

// Por si llega un avatar que esta versión de la app no sabe pintar
export const Desconocido = () => (
  <>
    <rect width="100" height="100" fill="#cfe3d6" />
    <circle cx="50" cy="42" r="16" fill="#9fb7a6" />
    <path d="M20,100 Q22,66 50,66 Q78,66 80,100 Z" fill="#9fb7a6" />
  </>
);

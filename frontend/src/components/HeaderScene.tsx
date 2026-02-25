function ResearcherFigure({ hairColor, shirtColor }: { hairColor: string; shirtColor: string }) {
  return (
    <g opacity={0.9}>
      <ellipse cx="0" cy="52" rx="9" ry="2.5" fill="rgba(0,0,0,0.05)" />

      <rect x="-5" y="37" width="4" height="13" rx="2" fill="#3d4560" />
      <rect x="1" y="37" width="4" height="13" rx="2" fill="#3d4560" />

      <ellipse cx="-3" cy="50.5" rx="3.5" ry="2" fill="#2a2a3a" />
      <ellipse cx="3" cy="50.5" rx="3.5" ry="2" fill="#2a2a3a" />

      <rect x="-9" y="17" width="18" height="22" rx="3.5" fill="#f5f5f5" stroke="#e6e6e6" strokeWidth="0.5" />

      <line x1="-9" y1="21" x2="-12" y2="33" stroke="#deb896" strokeWidth="2.8" strokeLinecap="round" />
      <line x1="9" y1="21" x2="12" y2="33" stroke="#deb896" strokeWidth="2.8" strokeLinecap="round" />
      <circle cx="-12" cy="33.5" r="2" fill="#e8c4a0" />
      <circle cx="12" cy="33.5" r="2" fill="#e8c4a0" />

      <polygon points="-5,17 5,17 0,22" fill={shirtColor} />

      <circle cx="0" cy="25" r="0.7" fill="#ddd" />
      <circle cx="0" cy="29" r="0.7" fill="#ddd" />
      <circle cx="0" cy="33" r="0.7" fill="#ddd" />

      <rect x="-2.5" y="13" width="5" height="5" rx="2" fill="#e8c4a0" />
      <circle cx="0" cy="8" r="8.5" fill="#e8c4a0" />

      <path d={`M-9,8 Q-9,-2 0,-5 Q9,-2 9,8 L7,5 Q4,3 0,2.5 Q-4,3 -7,5 Z`} fill={hairColor} />

      <circle cx="-3" cy="9.5" r="1.6" fill="#333" />
      <circle cx="3" cy="9.5" r="1.6" fill="#333" />
      <circle cx="-2.2" cy="8.8" r="0.6" fill="#fff" />
      <circle cx="3.8" cy="8.8" r="0.6" fill="#fff" />

      <circle cx="-5.5" cy="11.5" r="1.5" fill="rgba(255,180,170,0.25)" />
      <circle cx="5.5" cy="11.5" r="1.5" fill="rgba(255,180,170,0.25)" />

      <path d="M-1.5,13 Q0,14.2 1.5,13" fill="none" stroke="#c4a080" strokeWidth="0.5" strokeLinecap="round" />

      <g className="scene__speech">
        <circle cx="8" cy="-4" r="1.8" fill="#ccc" />
        <circle cx="13" cy="-7" r="1.8" fill="#ccc" />
        <circle cx="18" cy="-4" r="1.8" fill="#ccc" />
      </g>
    </g>
  )
}

function FmriProp() {
  return (
    <g>
      {/* Gantry housing */}
      <rect x="0" y="0" width="44" height="24" rx="4" fill="#e8edf2" stroke="#b0bcc8" strokeWidth="0.8" />
      {/* Bore outer */}
      <ellipse cx="16" cy="12" rx="8" ry="9" fill="#5a6a7a" />
      {/* Bore inner (depth) */}
      <ellipse cx="16" cy="12" rx="6" ry="7" fill="#3d4a5a" />
      {/* Scan line (animated) */}
      <line className="scene__scan-line" x1="10" y1="12" x2="22" y2="12" stroke="#44a1a0" strokeWidth="0.8" opacity="0.5" />
      {/* Patient bed */}
      <rect x="22" y="10" width="24" height="4" rx="1" fill="#c8d0d8" />
      {/* Base */}
      <rect x="-2" y="24" width="48" height="4" rx="2" fill="#99aabb" />
      {/* Status light */}
      <circle cx="36" cy="6" r="1.5" fill="#44a1a0" />
    </g>
  )
}

function LaptopProp() {
  return (
    <g>
      <rect x="0" y="0" width="34" height="22" rx="2.5" fill="#7a8a9a" />
      <rect x="2" y="2" width="30" height="18" rx="1.5" fill="#bde0ee" />
      <line x1="6" y1="8" x2="22" y2="8" stroke="#8cc" strokeWidth="1.2" strokeLinecap="round" opacity="0.4" />
      <line x1="6" y1="12" x2="26" y2="12" stroke="#8cc" strokeWidth="1.2" strokeLinecap="round" opacity="0.4" />
      <line x1="6" y1="16" x2="18" y2="16" stroke="#8cc" strokeWidth="1.2" strokeLinecap="round" opacity="0.4" />
      <rect x="-3" y="22" width="40" height="4" rx="2" fill="#5a6a7a" />
      <line className="scene__cursor" x1="8" y1="8" x2="8" y2="16" stroke="#0d5c63" strokeWidth="1.2" opacity="0.6" />
    </g>
  )
}

function WhiteboardProp() {
  return (
    <g>
      <rect x="0" y="0" width="56" height="40" rx="2.5" fill="#f8f8f8" stroke="#99aabb" strokeWidth="1.5" />
      <line
        className="scene__wb-line1"
        x1="8" y1="10" x2="42" y2="10"
        stroke="#0d5c63" strokeWidth="2" strokeLinecap="round"
        strokeDasharray="34"
      />
      <line
        className="scene__wb-line2"
        x1="8" y1="18" x2="46" y2="18"
        stroke="#c4783e" strokeWidth="2" strokeLinecap="round"
        strokeDasharray="38"
      />
      <line
        className="scene__wb-line3"
        x1="8" y1="26" x2="30" y2="26"
        stroke="#ffd166" strokeWidth="2" strokeLinecap="round"
        strokeDasharray="22"
      />
      <line
        className="scene__collab-line"
        x1="8" y1="33" x2="40" y2="33"
        stroke="#44a1a0" strokeWidth="1.8" strokeLinecap="round"
        strokeDasharray="32"
      />
      <line x1="16" y1="40" x2="16" y2="56" stroke="#99aabb" strokeWidth="1.8" />
      <line x1="40" y1="40" x2="40" y2="56" stroke="#99aabb" strokeWidth="1.8" />
      <line x1="10" y1="56" x2="22" y2="56" stroke="#99aabb" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="34" y1="56" x2="46" y2="56" stroke="#99aabb" strokeWidth="1.8" strokeLinecap="round" />
    </g>
  )
}

export function HeaderScene() {
  return (
    <svg
      className="topbar__scene"
      viewBox="0 0 500 65"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      <g transform="translate(24,30)" opacity={0.7}><FmriProp /></g>
      <g transform="translate(418,33)" opacity={0.7}><LaptopProp /></g>
      <g transform="translate(222,4)"><WhiteboardProp /></g>

      <g className="scene__r1">
        <ResearcherFigure hairColor="#2d3443" shirtColor="#0d5c63" />
      </g>
      <g className="scene__r2">
        <ResearcherFigure hairColor="#7a4422" shirtColor="#44a1a0" />
      </g>
    </svg>
  )
}

// One broad, swept fan blade pointing up from the hub. Its outer edge follows the
// casing ring. Six copies, 60 degrees apart, make the fan.
const BLADE =
  "M-1.23 -3.38Q-2.6 -8 0.41 -11.79A11.8 11.8 0 0 1 8.77 -7.9Q3.8 -7.6 1.52 -3.26Z";

export default function Wordmark({ size = 30, spinning = false }) {
  return (
    <div className="flex items-center gap-2.5">
      <svg
        width={size}
        height={size}
        viewBox="1.8 1.8 28.4 28.4"
        fill="none"
        aria-hidden="true"
        className="text-black"
      >
        {/* engine casing */}
        <circle cx="16" cy="16" r="12.9" stroke="currentColor" strokeWidth="2.2" />
        {/* the fan: only this part spins */}
        <g
          className={spinning ? "animate-spin" : ""}
          style={{ transformBox: "fill-box", transformOrigin: "center", animationDuration: "0.9s" }}
        >
          <g transform="translate(16 16)">
            {[0, 1, 2, 3, 4, 5].map((index) => (
              <path
                key={index}
                d={BLADE}
                fill="currentColor"
                transform={`rotate(${index * 60})`}
              />
            ))}
            {/* spinner */}
            <circle r="3" stroke="currentColor" strokeWidth="1.4" />
            <circle r="1.1" fill="currentColor" />
          </g>
        </g>
      </svg>
      <span className="font-serif text-[1.3rem] leading-none font-medium tracking-tight">
        First Solo
      </span>
    </div>
  );
}
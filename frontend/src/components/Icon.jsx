const PATHS = {
  plus: <path d="M12 5v14M5 12h14" />,
  trash: <path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />,
  upload: <path d="M12 16V4m0 0L7 9m5-5 5 5M5 20h14" />,
  file: <path d="M7 3h7l5 5v13H7zM14 3v5h5" />,
  up: <path d="M12 19V5m0 0-6 6m6-6 6 6" />,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  logout: <path d="M10 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4M15 8l4 4-4 4M19 12H9" />,
  copy: <path d="M9 9h10v10H9zM5 15V5h10" />,
  check: <path d="M5 12l4 4 10-10" />,
  chevron: <path d="M7 10l5 5 5-5" />,
  spinner: <path d="M12 3a9 9 0 1 0 9 9" />,
};

export default function Icon({ name, size = 18, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
}
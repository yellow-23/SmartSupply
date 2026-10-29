// Cargador de marca: el simbolo de SmartSupply (dos esquinas) se abre y cierra mientras gira.
// Usarlo en vez de un spinner generico cuando aun no se sabe si hay datos.
export default function BrandLoader({
  label = "Cargando...",
  hint,
  size = 52,
  className = "py-20",
}: {
  label?: string;
  hint?: string;
  size?: number;
  className?: string;
}) {
  return (
    <div role="status" aria-live="polite" className={`flex flex-col items-center justify-center gap-3 text-center ${className}`}>
      <svg viewBox="0 0 100 100" width={size} height={size} className="ss-loader" aria-hidden="true">
        <g fill="none" stroke="#EA580C" strokeWidth="19" strokeLinecap="round" strokeLinejoin="round">
          <path className="ss-loader-a" d="M30 46 V30 H46" />
          <path className="ss-loader-b" d="M70 54 V70 H54" />
        </g>
      </svg>
      <p className="text-sm font-medium text-gray-600">{label}</p>
      {hint && <p className="text-xs text-gray-400 max-w-xs">{hint}</p>}
    </div>
  );
}

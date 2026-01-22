import { useState } from 'react';
import FlyingPlane from './components/FlyingPlane';
import FallingPixels from './components/FallingPixels';

function App() {
  const [multiplier, setMultiplier] = useState<number | null>(null);
  const [history, setHistory] = useState<number[]>([]);

  const generateMultiplier = () => {
    const random = 1.01 + Math.random() * (12.01 - 1.01);
    const newMultiplier = Number(random.toFixed(2));
    setMultiplier(newMultiplier);
    setHistory((prev) => [newMultiplier, ...prev.slice(0, 19)]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-red-950 to-black flex items-center justify-center overflow-hidden relative">
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            'radial-gradient(circle at 20% 50%, rgba(220, 20, 60, 0.3) 0%, transparent 50%)',
        }}
      ></div>

      <FlyingPlane />
      <FallingPixels />

      {history.length > 0 && (
        <div className="absolute top-6 left-0 right-0 z-20 flex justify-center px-4">
          <div className="text-center">
            <p className="text-xs font-light text-white/70 mb-2 tracking-wide">
              История коэффициентов
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-md">
              {history.map((value, idx) => (
                <span key={idx} className="text-xs text-white/60 font-light">
                  {value.toFixed(2)}x{idx < history.length - 1 ? ',' : ''}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="relative z-10 flex flex-col items-center gap-8">
        {multiplier && (
          <div className="animate-scale-in">
            <div className="text-6xl font-bold text-white drop-shadow-2xl">
              {multiplier.toFixed(2)}x
            </div>
          </div>
        )}

        <button
          onClick={generateMultiplier}
          className="px-10 py-3 bg-gradient-to-r from-yellow-400 to-yellow-500 hover:from-yellow-500 hover:to-yellow-600 text-black text-xl font-bold rounded-2xl shadow-2xl transform transition-all hover:scale-105 active:scale-95"
        >
          Получить
        </button>
      </div>

      <style>{`
        @keyframes scale-in {
          0% {
            transform: scale(0.7);
            opacity: 0;
          }
          50% {
            transform: scale(1.1);
          }
          100% {
            transform: scale(1);
            opacity: 1;
          }
        }

        .animate-scale-in {
          animation: scale-in 0.5s ease-out;
        }
      `}</style>
    </div>
  );
}

export default App;

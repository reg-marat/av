import { useState } from 'react';
import FlyingPlane from './components/FlyingPlane';
import FallingPixels from './components/FallingPixels';
import PasswordGate from './components/PasswordGate';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [multiplier, setMultiplier] = useState<number | null>(null);
  const [history, setHistory] = useState<number[]>([]);
  const [animationKey, setAnimationKey] = useState(0);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [isPrecisionUpgraded, setIsPrecisionUpgraded] = useState(false);

  const generateMultiplier = () => {
    const random = 1.01 + Math.random() * (12.01 - 1.01);
    const newMultiplier = Number(random.toFixed(2));
    setMultiplier(newMultiplier);
    setAnimationKey((prev) => prev + 1);
    setHistory((prev) => [newMultiplier, ...prev.slice(0, 19)]);
  };

  if (!isAuthenticated) {
    return <PasswordGate onSuccess={() => setIsAuthenticated(true)} />;
  }

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

      <div className="relative z-10 flex flex-col items-center gap-6">
        {multiplier && (
          <div key={animationKey} className="animate-scale-in">
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

        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-3 shadow-2xl border border-white/20 max-w-sm w-full">
          <div className="text-center">
            {isPrecisionUpgraded ? (
              <p className="text-yellow-400 text-xs font-light leading-relaxed">
                Бот подключен и готов к работе. Текущая синхронизация коэффициентов - 99%
              </p>
            ) : (
              <>
                <p className="text-white/90 text-xs font-light leading-relaxed mb-3">
                  Бот подключен и готов к работе. Текущая синхронизация коэффициентов - 45%. Для синхронизации на 100% введи дополнительный пароль.
                </p>
                <button
                  onClick={() => setShowPasswordModal(true)}
                  className="w-full px-4 py-2 bg-gradient-to-r from-blue-400 to-blue-500 hover:from-blue-500 hover:to-blue-600 text-black font-bold rounded-xl shadow-lg transform transition-all hover:scale-105 active:scale-95 text-xs"
                >
                  Повысить точность до 100%
                </button>
              </>
            )}
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-3 shadow-2xl border border-white/20 max-w-sm w-full">
          <p className="text-center text-white/70 text-xs font-light">
            При возникновении вопросов - @kek13
          </p>
        </div>
      </div>

      {showPasswordModal && (
        <PasswordGate
          isModal={true}
          onClose={() => setShowPasswordModal(false)}
          onSuccess={() => {
            setIsPrecisionUpgraded(true);
            setShowPasswordModal(false);
          }}
          correctPassword="2801"
          title="Введите пароль"
        />
      )}

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

export default function FlyingPlane() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      <div className="plane-container">
        <img
          src="https://i.postimg.cc/y8pzB2yh/Fon.png"
          alt="Flying plane"
          width="80"
          height="60"
        />
      </div>
      <style>{`
        .plane-container {
          position: absolute;
          animation: flyPlane 15s linear infinite;
          filter: drop-shadow(0 2px 8px rgba(255, 215, 0, 0.6));
        }

        @keyframes flyPlane {
          0% {
            left: -10%;
            top: 20%;
            transform: rotate(-15deg);
          }
          25% {
            left: 30%;
            top: 10%;
            transform: rotate(-5deg);
          }
          50% {
            left: 60%;
            top: 25%;
            transform: rotate(-20deg);
          }
          75% {
            left: 90%;
            top: 15%;
            transform: rotate(-10deg);
          }
          100% {
            left: 120%;
            top: 30%;
            transform: rotate(-15deg);
          }
        }
      `}</style>
    </div>
  );
}

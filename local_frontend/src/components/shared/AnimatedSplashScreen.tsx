import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';

interface AnimatedSplashScreenProps {
  onComplete: () => void;
  isLoading: boolean;
}

interface OrbitConfig {
  radius: number;
  size: number;
  duration: number;
  delay: number;
  glow: string;
}

const LOADING_BEATS = [
  'Synchronising command uplinks...',
  'Awakening agent cohorts...',
  'Mapping multiversal theatres...',
  'Priming tool arsenals...',
  'Orbit achieved. Deploying interface...'
];

export const AnimatedSplashScreen: React.FC<AnimatedSplashScreenProps> = ({ onComplete, isLoading }) => {
  const [progress, setProgress] = useState(0);
  const [beatIndex, setBeatIndex] = useState(0);
  const prefersReducedMotion = useReducedMotion();

  const viewport = useMemo(
    () => ({
      width: typeof window !== 'undefined' ? window.innerWidth : 1920,
      height: typeof window !== 'undefined' ? window.innerHeight : 1080,
    }),
    []
  );

  const orbitConfig = useMemo<OrbitConfig[]>(
    () => [
      { radius: 110, size: 10, duration: 18, delay: 0, glow: 'from-cyan-400 to-indigo-500' },
      { radius: 160, size: 14, duration: 24, delay: 4, glow: 'from-purple-400 to-indigo-500' },
      { radius: 215, size: 18, duration: 32, delay: 8, glow: 'from-pink-500 to-rose-500' },
    ],
    []
  );

  useEffect(() => {
    if (!isLoading) return;

    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + 4 + Math.random() * 2;
        if (next >= 100) {
          clearInterval(progressTimer);
          setTimeout(() => onComplete(),700);
          return 100;
        }
        return next;
      });
    }, 250);

    return () => clearInterval(progressTimer);
  }, [isLoading, onComplete]);

  useEffect(() => {
    if (!isLoading) return;

    const beatTimer = setInterval(() => {
      setBeatIndex((prev) => (prev + 1) % LOADING_BEATS.length);
    }, 1400);

    return () => clearInterval(beatTimer);
  }, [isLoading]);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [readyToPlay, setReadyToPlay] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      setReadyToPlay(false);
      return;
    }

    setReadyToPlay(true);
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      audioRef.current = null;
    };
  }, [isLoading]);

  useEffect(() => {
    if (!readyToPlay) return;

    const handleFirstInteraction = () => {
      const audio = new Audio('/audio/agentverse-launch.mp3');
      audio.loop = false;
      audio.volume = 0.6;
      audioRef.current = audio;

      audio.play().catch((error) => {
        console.warn('Splash audio could not start automatically. User interaction may be required.', error);
      });

      audio.addEventListener('ended', () => {
        setReadyToPlay(false);
        audioRef.current = null;
      }, { once: true });

      window.removeEventListener('pointerdown', handleFirstInteraction);
      window.removeEventListener('keydown', handleFirstInteraction);
    };

    window.addEventListener('pointerdown', handleFirstInteraction, { once: true });
    window.addEventListener('keydown', handleFirstInteraction, { once: true });

    return () => {
      window.removeEventListener('pointerdown', handleFirstInteraction);
      window.removeEventListener('keydown', handleFirstInteraction);
    };
  }, [readyToPlay]);

  const displayProgress = Math.min(Math.round(progress), 100);

  if (!isLoading) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.6, ease: 'easeInOut' }}
        className="fixed inset-0 z-[100] flex items-center justify-center overflow-hidden bg-slate-950"
      >
        <div className="absolute inset-0 brand-gradient-soft opacity-70 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(30,64,175,0.35),_transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_rgba(236,72,153,0.25),_transparent_65%)] mix-blend-screen opacity-60" />

        {/* Starfield */}
        {!prefersReducedMotion && (
          <div className="pointer-events-none absolute inset-0 overflow-hidden">
            {Array.from({ length: 60 }).map((_, idx) => (
              <motion.span
                key={idx}
                className="absolute h-0.5 w-0.5 rounded-full bg-white/60"
                initial={{
                  x: Math.random() * viewport.width,
                  y: Math.random() * viewport.height,
                  opacity: Math.random() * 0.6 + 0.2,
                }}
                animate={{
                  y: Math.random() * viewport.height,
                  opacity: [0.2, 0.8, 0.2],
                }}
                transition={{
                  duration: Math.random() * 8 + 6,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </div>
        )}

        <div className="relative z-10 flex w-full max-w-6xl flex-col items-center gap-12 px-6 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.94, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.7, ease: 'easeOut' }}
            className="relative flex h-56 w-56 items-center justify-center rounded-full brand-surface-strong shadow-2xl ring-2 ring-white/10"
          >
            <motion.div
              animate={{ rotate: prefersReducedMotion ? 0 : 360 }}
              transition={{
                duration: prefersReducedMotion ? 0.01 : 24,
                repeat: prefersReducedMotion ? 0 : Infinity,
                ease: 'linear',
              }}
              className="absolute inset-6 rounded-full border border-white/15"
            />
            <motion.div
              animate={
                prefersReducedMotion
                  ? { opacity: 0.75 }
                  : { scale: [0.95, 1.06, 0.95], opacity: [0.5, 0.9, 0.5] }
              }
              transition={{
                duration: prefersReducedMotion ? 0.01 : 3,
                repeat: prefersReducedMotion ? 0 : Infinity,
                ease: 'easeInOut',
              }}
              className="absolute inset-10 rounded-full brand-gradient blur-xl opacity-90"
            />
            <div className="relative flex h-40 w-40 items-center justify-center rounded-full brand-glass">
              <img
                src="/logo-icon.svg"
                alt="AgentVerse"
                className="h-16 w-16 drop-shadow-[0_0_24px_rgba(129,140,248,0.6)]"
              />
            </div>
            {!prefersReducedMotion &&
              orbitConfig.map(({ radius, size, duration, delay, glow }) => (
                <motion.div
                  key={`${radius}-${size}`}
                  className="absolute flex items-center justify-center"
                  style={{ width: radius * 2, height: radius * 2 }}
                  animate={{ rotate: 360 }}
                  transition={{ duration, delay, repeat: Infinity, ease: 'linear' }}
                >
                  <div className="relative h-full w-full">
                    <div className="absolute inset-0 rounded-full border border-white/5" />
                    <div
                      className={`absolute left-1/2 top-0 -translate-x-1/2 rounded-full bg-gradient-to-br ${glow} shadow-[0_0_32px_rgba(147,197,253,0.35)]`}
                      style={{ width: size, height: size }}
                    />
                  </div>
                </motion.div>
              ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.7, ease: 'easeOut' }}
            className="w-full max-w-xl rounded-3xl brand-surface px-8 py-7 shadow-2xl"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.45em] text-slate-500 dark:text-slate-400">
              AgentVerse Launch Systems
            </p>
            <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">
              Deploying the Multiverse Console
            </h1>
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-300">
              Calibrating orchestration engines, secure channels, and collaborative theatres.
            </p>

            <div className="mt-8 space-y-4 text-left">
              <div className="h-2.5 overflow-hidden rounded-full brand-progress-track">
                <motion.div
                  className="brand-progress-fill h-full rounded-full"
                  initial={{ width: '0%' }}
                  animate={{ width: `${displayProgress}%` }}
                  transition={{ ease: 'easeOut', duration: 0.45 }}
                />
              </div>
              <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400">
                <span>{displayProgress}% Ready</span>
                <span>Systems Online</span>
              </div>
              <motion.p
                key={beatIndex}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.4 }}
                className="text-sm font-medium text-slate-600 dark:text-slate-200"
              >
                {LOADING_BEATS[beatIndex]}
              </motion.p>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

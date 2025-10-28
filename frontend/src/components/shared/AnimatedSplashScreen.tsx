import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

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

  const viewport = useMemo(
    () => ({
      width: typeof window !== 'undefined' ? window.innerWidth : 1920,
      height: typeof window !== 'undefined' ? window.innerHeight : 1080,
    }),
    []
  );

  const orbitConfig = useMemo<OrbitConfig[]>(
    () => [
      { radius: 110, size: 10, duration: 18, delay: 0, glow: 'from-cyan-400 to-blue-500' },
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

  if (!isLoading) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.6, ease: 'easeInOut' }}
        className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950"
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(88,28,135,0.3),_transparent_55%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_rgba(56,189,248,0.2),_transparent_60%)]" />

        {/* Starfield */}
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

        <div className="relative flex flex-col items-center text-center">
          {/* Core */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="relative flex h-52 w-52 items-center justify-center rounded-full bg-slate-900/70 shadow-[0_0_120px_rgba(99,102,241,0.45)] ring-2 ring-indigo-500/30"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 26, repeat: Infinity, ease: 'linear' }}
              className="absolute inset-6 rounded-full border border-indigo-500/30"
            />
            <motion.div
              animate={{ scale: [0.96, 1.04, 0.96], opacity: [0.5, 0.85, 0.5] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute inset-8 rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 blur-xl"
            />
            <img
              src="/logo-icon.svg"
              alt="AgentVerse"
              className="relative h-16 w-16 drop-shadow-[0_0_20px_rgba(129,140,248,0.65)]"
            />
          </motion.div>

          {/* Orbits */}
          {orbitConfig.map(({ radius, size, duration, delay, glow }) => (
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
                  className={`absolute left-1/2 top-0 -translate-x-1/2 rounded-full bg-gradient-to-br ${glow} shadow-[0_0_25px_rgba(147,197,253,0.4)]`}
                  style={{ width: size, height: size }}
                />
              </div>
            </motion.div>
          ))}

          {/* Title */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="mt-16"
          >
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Deploying the Agent Multiverse
            </h1>
            <p className="mt-3 text-sm text-slate-300">
              Synchronising neural fleets across timelines and task theatres.
            </p>
          </motion.div>

          {/* Progress */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
            className="mt-10 w-80 max-w-[90vw] space-y-4"
          >
            <div className="h-2.5 overflow-hidden rounded-full bg-white/10">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-indigo-400 to-pink-400 shadow-[0_0_25px_rgba(96,165,250,0.45)]"
                initial={{ width: '0%' }}
                animate={{ width: `${Math.min(progress, 100)}%` }}
                transition={{ ease: 'easeOut', duration: 0.35 }}
              />
            </div>
            <div className="flex items-center justify-between text-xs font-medium text-slate-300">
              <span>{Math.round(progress)}%</span>
              <span className="uppercase tracking-[0.2em] text-slate-400">Launch sequence</span>
            </div>
            <motion.p
              key={beatIndex}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.4 }}
              className="text-sm text-slate-200"
            >
              {LOADING_BEATS[beatIndex]}
            </motion.p>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

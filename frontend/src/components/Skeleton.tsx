interface SkeletonProps {
  className?: string;
}

export default function Skeleton({ className = "" }: SkeletonProps) {
  return <div className={`animate-pulse bg-surface-variant rounded-lg ${className}`} />;
}

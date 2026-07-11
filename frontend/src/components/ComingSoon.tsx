interface ComingSoonProps {
  title: string;
  description: string;
}

export default function ComingSoon({ title, description }: ComingSoonProps) {
  return (
    <div className="pt-24 pb-stack-lg px-container-padding flex-1">
      <div className="mb-stack-lg">
        <h2 className="font-headline-lg text-headline-lg text-on-surface font-bold">{title}</h2>
        <p className="text-body-md text-on-surface-variant">{description}</p>
      </div>
      <div className="flex items-center justify-center h-64 bg-surface-container-low border border-dashed border-outline-variant rounded-xl text-on-surface-variant text-body-md">
        En construcción — próxima fase del plan.
      </div>
    </div>
  );
}

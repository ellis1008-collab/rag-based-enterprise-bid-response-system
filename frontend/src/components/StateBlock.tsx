type StateBlockProps = {
  title: string;
  body?: string;
};

export function LoadingBlock({ title = "加载中" }: Partial<StateBlockProps>) {
  return (
    <div className="rounded-md border border-bidpilot-line bg-white p-6 text-sm text-slate-600">
      {title}...
    </div>
  );
}

export function ErrorBlock({ title, body }: StateBlockProps) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-6 text-sm text-red-700">
      <div className="font-semibold">{title}</div>
      {body ? <div className="mt-2 text-red-600">{body}</div> : null}
    </div>
  );
}

export function EmptyBlock({ title, body }: StateBlockProps) {
  return (
    <div className="rounded-md border border-dashed border-bidpilot-line bg-white p-6 text-sm text-slate-500">
      <div className="font-medium text-slate-700">{title}</div>
      {body ? <div className="mt-2">{body}</div> : null}
    </div>
  );
}

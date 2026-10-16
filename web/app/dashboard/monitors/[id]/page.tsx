import { MonitorDetailClient } from "./MonitorDetailClient";

export default async function MonitorDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <MonitorDetailClient monitorId={id} />;
}

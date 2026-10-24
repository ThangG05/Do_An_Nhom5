import PostPermalink from './PostPermalink';

export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PostPermalink id={id} />;
}

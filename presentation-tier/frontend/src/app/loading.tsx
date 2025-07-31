export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center space-y-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-customs-600 border-r-transparent"></div>
        <p className="text-sm text-muted-foreground">시스템을 불러오는 중...</p>
      </div>
    </div>
  );
}
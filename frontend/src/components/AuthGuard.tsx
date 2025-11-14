'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // 認証不要なパス
    const publicPaths = ['/auth/login', '/auth/register'];
    const isPublicPath = publicPaths.includes(pathname);

    if (!isPublicPath && !isAuthenticated()) {
      router.push('/auth/login');
    } else {
      setIsChecking(false);
    }
  }, [pathname, router]);

  if (isChecking) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  return <>{children}</>;
}

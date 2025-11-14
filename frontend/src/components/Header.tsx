'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { getCurrentUser, logout, User } from '@/lib/auth';

export default function Header() {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const isAuthPage = pathname.startsWith('/auth');

  useEffect(() => {
    if (!isAuthPage) {
      loadUser();
    }
  }, [isAuthPage]);

  const loadUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (err) {
      console.error('Failed to load user:', err);
    }
  };

  const handleLogout = () => {
    if (confirm('ログアウトしますか？')) {
      logout();
    }
  };

  if (isAuthPage) {
    return null;
  }

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/">
              <h1 className="text-xl font-bold text-gray-900 cursor-pointer hover:text-gray-700">
                Project Transparency
              </h1>
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            {user && (
              <>
                <span className="text-sm text-gray-700">
                  {user.name}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md hover:bg-gray-100 transition-colors"
                >
                  ログアウト
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

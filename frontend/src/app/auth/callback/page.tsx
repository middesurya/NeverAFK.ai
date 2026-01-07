'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';

const LoadingSpinner = () => (
  <svg className="w-8 h-8 animate-spin text-violet-500" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const ErrorIcon = () => (
  <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Verifying your email...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check if Supabase is configured
        if (!supabase) {
          setStatus('error');
          setMessage('Authentication is not configured. Please contact support.');
          return;
        }

        // Check for error in URL params
        const error = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');

        if (error) {
          setStatus('error');
          setMessage(errorDescription || 'An error occurred during email verification');
          return;
        }

        // Check for hash fragment (Supabase sometimes uses this)
        const hash = window.location.hash;
        if (hash) {
          const hashParams = new URLSearchParams(hash.substring(1));
          const hashError = hashParams.get('error');
          const hashErrorDescription = hashParams.get('error_description');

          if (hashError) {
            setStatus('error');
            setMessage(hashErrorDescription || 'An error occurred during email verification');
            return;
          }

          // If there's an access_token in the hash, Supabase will handle it
          const accessToken = hashParams.get('access_token');
          if (accessToken) {
            // Wait for Supabase to process the token
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }

        // Check if user is now authenticated
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) {
          setStatus('error');
          setMessage(sessionError.message);
          return;
        }

        if (session) {
          setStatus('success');
          setMessage('Email verified successfully! Redirecting to dashboard...');
          setTimeout(() => {
            router.push('/dashboard');
          }, 2000);
        } else {
          // No session but no error - might need to log in
          setStatus('success');
          setMessage('Email verified! Please log in to continue.');
          setTimeout(() => {
            router.push('/login');
          }, 2000);
        }
      } catch (err) {
        setStatus('error');
        setMessage('An unexpected error occurred. Please try again.');
        console.error('Auth callback error:', err);
      }
    };

    handleCallback();
  }, [router, searchParams]);

  return (
    <div className="text-center px-6">
      <div className="w-16 h-16 rounded-full bg-[var(--color-bg-secondary)] flex items-center justify-center mx-auto mb-6">
        {status === 'loading' && <LoadingSpinner />}
        {status === 'success' && <CheckIcon />}
        {status === 'error' && <ErrorIcon />}
      </div>

      <h1 className="text-xl font-bold text-[var(--color-text-primary)] mb-2">
        {status === 'loading' && 'Verifying...'}
        {status === 'success' && 'Success!'}
        {status === 'error' && 'Verification Failed'}
      </h1>

      <p className="text-[var(--color-text-secondary)] mb-6 max-w-md">
        {message}
      </p>

      {status === 'error' && (
        <div className="space-y-3">
          <button
            onClick={() => router.push('/signup')}
            className="btn btn-primary px-6 py-2"
          >
            Try signing up again
          </button>
          <p className="text-sm text-[var(--color-text-muted)]">
            or{' '}
            <button
              onClick={() => router.push('/login')}
              className="text-[var(--color-accent-light)] hover:underline"
            >
              go to login
            </button>
          </p>
        </div>
      )}
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] flex items-center justify-center">
      <Suspense fallback={
        <div className="text-center px-6">
          <div className="w-16 h-16 rounded-full bg-[var(--color-bg-secondary)] flex items-center justify-center mx-auto mb-6">
            <LoadingSpinner />
          </div>
          <h1 className="text-xl font-bold text-[var(--color-text-primary)] mb-2">
            Loading...
          </h1>
        </div>
      }>
        <AuthCallbackContent />
      </Suspense>
    </div>
  );
}

/**
 * Root Page
 *
 * Redirects to dashboard
 */

import { redirect } from 'next/navigation';

export default function RootPage() {
  redirect('/projects');
}

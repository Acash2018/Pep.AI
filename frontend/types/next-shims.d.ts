declare module 'next' {
  export type Metadata = {
    title?: string;
    description?: string;
    [key: string]: unknown;
  };
}

declare module 'next/link' {
  import type { AnchorHTMLAttributes, ReactNode } from 'react';

  type LinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
    children?: ReactNode;
  };

  export default function Link(props: LinkProps): JSX.Element;
}

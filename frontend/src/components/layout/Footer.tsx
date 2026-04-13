import { Shield } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-2">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Traffic Justice AI &mdash; Promoting legal transparency for Indian drivers
              </span>
            </div>
            <span className="text-xs text-muted-foreground sm:border-l sm:border-border sm:pl-2">
              © {new Date().getFullYear()}{" "}
              <a
                href="https://indianaiproduction.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-foreground"
              >
                Indian AI Production
              </a>
            </span>
          </div>
          <p className="text-xs text-muted-foreground max-w-md text-center md:text-right">
            This platform provides informational assistance only and does not constitute legal
            advice. Always consult a qualified legal professional for specific legal matters.
          </p>
        </div>
      </div>
    </footer>
  );
}

import { Link } from "react-router-dom";
import { BrandMark } from "../components/ui";

export function NotFoundPage() {
  return (
    <section className="hero-panel mx-auto max-w-xl text-center">
      <div className="mx-auto w-fit">
        <BrandMark size={42} />
      </div>
      <p className="kicker mt-4">404</p>
      <h1 className="hero-title mx-auto">This page is not part of CryptoGuard</h1>
      <p className="lede mx-auto">
        The address does not match a verification workspace. Return to the dashboard to hash a file, check an HMAC tag, or verify a signature.
      </p>
      <div className="mt-5 flex justify-center">
        <Link className="btn btn-primary" to="/">Back to dashboard</Link>
      </div>
    </section>
  );
}

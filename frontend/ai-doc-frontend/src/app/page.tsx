import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  return (
    <>
      <Navbar />
      <section className="min-h-[80vh] flex flex-col justify-center items-center text-center px-4">
        <h1 className="text-5xl font-bold max-w-3xl text-gray-900">
          Generate Clean, Smart Documentation From Your Codebase
        </h1>
        <p className="text-gray-500 max-w-xl mt-4">
          AI-powered documentation generator for developers. Connect your repo, pick a branch, and get instant docs.
        </p>

        <Link href="/auth/login">
          <Button className="mt-6 px-8 text-lg bg-indigo-600 hover:bg-indigo-700" >
           Get Started
           </Button>
        </Link>
      </section>
    </>
  );
}

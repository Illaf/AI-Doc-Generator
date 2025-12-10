"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { api } from "../../lib/api";
import { saveToken } from "../../lib/auth";

export default function Callback() {
  const params = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const code = params.get("code");
    if (!code) return;

    api.get(`/auth/github/callback?code=${code}`)
      .then((res) => {
        saveToken(res.data.token);
        router.replace("/dashboard");
      })
      .catch(() => router.replace("/auth/login"));
  }, []);

  return <p>Logging you in...</p>;
}

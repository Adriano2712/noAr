"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { useAuth } from "@/lib/auth/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();

  return (
    <AuthForm
      title="Entrar"
      submitLabel="Entrar"
      submittingLabel="Entrando..."
      onSubmit={async (email, password) => {
        await login(email, password);
        router.push("/dashboard");
      }}
      footer={
        <>
          Não tem conta?{" "}
          <Link href="/register" className="font-medium underline">
            Criar conta
          </Link>
        </>
      }
    />
  );
}

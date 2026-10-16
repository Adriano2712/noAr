"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { useAuth } from "@/lib/auth/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();

  return (
    <AuthForm
      title="Criar conta"
      submitLabel="Criar conta"
      submittingLabel="Criando..."
      onSubmit={async (email, password) => {
        await register(email, password);
        router.push("/dashboard");
      }}
      footer={
        <>
          Já tem conta?{" "}
          <Link href="/login" className="font-medium underline">
            Entrar
          </Link>
        </>
      }
    />
  );
}

import { LoginForm } from "@/components/features/login-form";

export default function LoginPage() {
  return (
    <div className="max-w-sm mx-auto px-4 py-20">
      <h1 className="font-serif text-3xl font-bold text-text-primary text-center mb-8">
        Log in
      </h1>
      <LoginForm />
    </div>
  );
}

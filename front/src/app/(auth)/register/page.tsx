import { RegisterForm } from "@/components/features/register-form";

export default function RegisterPage() {
  return (
    <div className="max-w-sm mx-auto px-4 py-20">
      <h1 className="font-serif text-3xl font-bold text-text-primary text-center mb-8">
        Create your account
      </h1>
      <RegisterForm />
    </div>
  );
}

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, EyeOff, Sparkles, User, Lock, ArrowRight, ShieldCheck, Moon, Sun } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      toast.error("Please fill in all fields");
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setIsLoading(true);
    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const resData = await response.json();

      if (response.ok && resData.status === "success") {
        if (isLogin) {
          localStorage.setItem("session_token", resData.data.token);
          localStorage.setItem("user", JSON.stringify(resData.data.user));
          toast.success("Welcome back! Cosmic portal active.");
          navigate("/");
        } else {
          toast.success("Registration successful! Initiating first login...");
          // Auto login after registration
          const loginResponse = await fetch("/api/auth/login", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
          });
          const loginData = await loginResponse.json();
          if (loginResponse.ok && loginData.status === "success") {
            localStorage.setItem("session_token", loginData.data.token);
            localStorage.setItem("user", JSON.stringify(loginData.data.user));
            navigate("/");
          } else {
            setIsLogin(true);
            setConfirmPassword("");
          }
        }
      } else {
        toast.error(resData.message || "An authentication error occurred");
      }
    } catch (error) {
      console.error(error);
      toast.error("Unable to connect to the backend server.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuestDemo = async () => {
    setIsLoading(true);
    // Generate a random guest username to ensure unique data isolation per guest login
    const randomSuffix = Math.floor(1000 + Math.random() * 9000);
    const guestUser = `explorer_${randomSuffix}`;
    const guestPass = "explorerPass123";

    try {
      // 1. Try to Register the Guest
      const regResponse = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: guestUser, password: guestPass }),
      });

      // 2. Log in the Guest
      const loginResponse = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: guestUser, password: guestPass }),
      });

      const loginData = await loginResponse.json();
      if (loginResponse.ok && loginData.status === "success") {
        localStorage.setItem("session_token", loginData.data.token);
        localStorage.setItem("user", JSON.stringify(loginData.data.user));
        toast.success(`Logged in as Guest Explorer: ${guestUser}`);
        navigate("/");
      } else {
        toast.error("Failed to start Guest session");
      }
    } catch (error) {
      toast.error("Could not activate Guest Demo mode");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0a0518] font-sans selection:bg-purple-500 selection:text-white">
      {/* Animated Floating Gradients (Nebula Effect) */}
      <div className="absolute top-[-20%] left-[-10%] w-[60vw] h-[60vw] rounded-full bg-gradient-to-tr from-violet-800/20 to-indigo-900/10 blur-[120px] animate-pulse duration-[8000ms] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-gradient-to-bl from-pink-800/10 to-orange-800/20 blur-[100px] animate-pulse duration-[6000ms] pointer-events-none" />
      <div className="absolute top-[30%] right-[20%] w-[35vw] h-[35vw] rounded-full bg-gradient-to-br from-purple-800/15 to-blue-900/10 blur-[130px] pointer-events-none" />

      {/* Background Starry Particles */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiB2aWV3Qm94PSIwIDAgMjAwIDIwMCI+PGNpcmNsZSBjeD0iMTAiIGN5PSIxMCIgcj0iMSIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjE1KSIvPjxjaXJjbGUgY3g9IjcwIiBjeT0iMTIwIiByPSIxLjUiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4yKSIvPjxjaXJjbGUgY3g9IjE0MCIgY3k9IjQwIiByPSIwLjgiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4xKSIvPjxjaXJjbGUgY3g9IjE4MCIgY3k9IjE2MCIgcj0iMS4yIiBmaWxsPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMTUpIi8+PC9zdmc+')] opacity-40" />

      {/* Main Glassmorphic Wrapper */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-10 w-full max-w-[450px] p-1 px-4 sm:px-0"
      >
        <div className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.03] p-8 shadow-2xl backdrop-blur-2xl sm:p-10 hover:border-white/[0.12] transition-colors duration-500">
          
          {/* Top cosmic card edge highlight */}
          <div className="absolute top-0 left-0 right-0 h-[1.5px] bg-gradient-to-r from-transparent via-purple-500 to-transparent opacity-80" />

          {/* Logo & Header */}
          <div className="text-center mb-8">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ repeat: Infinity, duration: 40, ease: "linear" }}
              className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-pink-500 mb-4 shadow-lg shadow-purple-900/30"
            >
              <Sparkles className="w-6 h-6 text-white" />
            </motion.div>
            
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Cosmic Ideas
            </h1>
            <p className="text-sm text-slate-400 mt-2">
              Theory-to-Reality Evolution Portal
            </p>
          </div>

          {/* Tab Selector */}
          <div className="grid grid-cols-2 p-1 bg-white/[0.05] rounded-xl mb-6 border border-white/[0.05]">
            <button
              onClick={() => { setIsLogin(true); setConfirmPassword(""); }}
              className={`py-2 text-sm font-semibold rounded-lg transition-all duration-300 ${
                isLogin
                  ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`py-2 text-sm font-semibold rounded-lg transition-all duration-300 ${
                !isLogin
                  ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Register
            </button>
          </div>

          {/* Auth Form */}
          <form onSubmit={handleAuth} className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-300 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-purple-400" /> Username
              </Label>
              <div className="relative">
                <Input
                  type="text"
                  placeholder="Enter username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="bg-white/[0.03] border-white/[0.08] text-white placeholder:text-slate-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl pl-4 py-6"
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-slate-300 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-purple-400" /> Password
              </Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-white/[0.03] border-white/[0.08] text-white placeholder:text-slate-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl pl-4 pr-12 py-6"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Confirm Password (only on Register) */}
            <AnimatePresence>
              {!isLogin && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-2"
                >
                  <Label className="text-slate-300 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-purple-400" /> Confirm Password
                  </Label>
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="bg-white/[0.03] border-white/[0.08] text-white placeholder:text-slate-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl pl-4 py-6"
                    disabled={isLoading}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-500 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-6 rounded-xl transition-all duration-300 shadow-lg shadow-purple-900/20 hover:shadow-purple-900/40 transform hover:-translate-y-[1px] active:translate-y-0"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Aligning stars...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2 text-sm uppercase tracking-wider">
                  {isLogin ? "Enter Portal" : "Assemble Account"}
                  <ArrowRight className="w-4 h-4" />
                </span>
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative flex items-center justify-center my-6">
            <div className="w-full border-t border-white/[0.06]" />
            <span className="absolute px-3 bg-[#0a0518] text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
              Or Explore Instantly
            </span>
          </div>

          {/* Guest Demo button */}
          <Button
            type="button"
            variant="outline"
            onClick={handleGuestDemo}
            disabled={isLoading}
            className="w-full border-dashed border-white/[0.12] bg-white/[0.01] hover:bg-white/[0.05] text-purple-300 hover:text-purple-200 hover:border-purple-500/[0.3] py-6 rounded-xl font-medium transition-all duration-300"
          >
            <Sparkles className="w-4 h-4 mr-2 text-pink-400 animate-pulse" />
            Launch Guest Demo
          </Button>

          {/* Footer note */}
          <p className="text-[11px] text-center text-slate-500 mt-6 leading-relaxed">
            Every account gets its own independent database store on MongoDB Atlas. Zero overlap, absolute privacy.
          </p>
        </div>
      </motion.div>
    </div>
  );
}

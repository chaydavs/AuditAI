import React, { useState } from 'react';
import { motion } from 'framer-motion';

const LandingPage = () => {
    const [step, setStep] = useState(1);
    const [email, setEmail] = useState('');
    const [formData, setFormData] = useState({ major: '', goal: '' });
    const [status, setStatus] = useState(null);

    // YOUR GOOGLE SCRIPT URL
    const GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyOoxPZjIwHNVYdkKFn710eKaIReBUllb_3jVvgd_-3NWzHb9RQJvrfWPkKiewKJOYt2Q/exec";

    const handleSubmit = async () => {
        if (!email || !email.includes('@')) {
            alert("Please enter a valid email.");
            return;
        }

        setStatus('loading');

        try {
            await fetch(GOOGLE_SCRIPT_URL, {
                method: "POST",
                mode: "no-cors",
                headers: { "Content-Type": "text/plain" },
                body: JSON.stringify({
                    major: formData.major,
                    goal: formData.goal,
                    email: email,
                    timestamp: new Date().toISOString()
                }),
            });

            setStatus('success');
            setEmail('');

        } catch (error) {
            console.error("Submission Error:", error);
            setStatus('error');
        }
    };

    // --- STEP 1: THE "CLASSY" HOOK ---
    if (step === 1) {
        return (
            <div className="min-h-screen bg-[#FDFCF8] text-slate-900 font-sans flex flex-col items-center justify-center p-6">
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    className="max-w-xl w-full"
                >
                    {/* Handwritten-style Box Border */}
                    <div className="border border-slate-900 p-8 md:p-12 relative shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] bg-white">

                        {/* The "Classy" Title */}
                        <h1 className="text-4xl md:text-5xl font-serif font-medium text-center mb-6 leading-tight">
                            Advising, <span className="italic">made better.</span>
                        </h1>

                        {/* The Divider Line */}
                        <div className="w-24 h-px bg-slate-900 mx-auto mb-6"></div>

                        {/* The Pitch */}
                        <p className="text-lg text-center text-slate-700 font-light mb-10 leading-relaxed">
                            We're building an AI advisor to help you make better decisions, save time, and money.
                        </p>

                        {/* The Form */}
                        <div className="space-y-6">
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Your Major</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Economics"
                                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-lg placeholder:font-light"
                                    value={formData.major}
                                    onChange={(e) => setFormData({ ...formData, major: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Career Goal</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Investment Banking"
                                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-lg placeholder:font-light"
                                    value={formData.goal}
                                    onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
                                />
                            </div>

                            <button
                                onClick={() => {
                                    if (formData.major && formData.goal) setStep(2);
                                    else alert("Please fill in both fields first.");
                                }}
                                className="w-full py-4 bg-slate-900 text-white font-serif text-lg hover:bg-slate-800 transition-all mt-4"
                            >
                                Create My Plan
                            </button>
                        </div>
                    </div>
                </motion.div>
            </div>
        );
    }

    // --- STEP 2: THE "EXCLUSIVE" GATE ---
    return (
        <div className="min-h-screen bg-[#FDFCF8] flex flex-col items-center justify-center p-6 text-slate-900 font-sans">
            <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-lg w-full"
            >
                <div className="border border-slate-900 bg-white p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] text-center">

                    <h2 className="text-3xl font-serif mb-4">Strategy Generated.</h2>
                    <p className="text-slate-600 font-light mb-8">
                        We have identified a path for a <span className="font-medium text-slate-900">{formData.major}</span> major aiming for <span className="font-medium text-slate-900">{formData.goal}</span>.
                    </p>

                    {/* Locked Content Visual (Classy Style) */}
                    <div className="bg-slate-50 p-6 border border-slate-100 mb-8 relative">
                        <div className="space-y-4 filter blur-[3px] opacity-40">
                            <div className="h-4 bg-slate-300 w-3/4 mx-auto"></div>
                            <div className="h-4 bg-slate-300 w-1/2 mx-auto"></div>
                            <div className="h-4 bg-slate-300 w-5/6 mx-auto"></div>
                        </div>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="bg-white border border-slate-200 px-4 py-2 shadow-sm">
                                <span className="font-serif text-sm">🔒 Waitlist Access Only</span>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <input
                            type="email"
                            placeholder="Enter your email"
                            className="w-full text-center border border-slate-300 p-3 focus:outline-none focus:border-slate-900 transition-colors"
                            value={email}
                            disabled={status === 'success'}
                            onChange={(e) => setEmail(e.target.value)}
                        />

                        <button
                            onClick={handleSubmit}
                            disabled={status === 'loading' || status === 'success'}
                            className={`w-full py-4 font-serif text-lg transition-all ${status === 'success'
                                ? 'bg-green-700 text-white'
                                : 'bg-slate-900 text-white hover:bg-slate-800'
                                }`}
                        >
                            {status === 'loading' ? 'Processing...' : status === 'success' ? 'You are on the list.' : 'Join Waitlist'}
                        </button>

                        {status === 'error' && (
                            <p className="text-red-500 text-sm font-serif italic">Something went wrong. Please try again.</p>
                        )}
                    </div>

                    {/* Subtle Upsell */}
                    <div className="mt-8 pt-6 border-t border-slate-100">
                        <button
                            onClick={() => window.open('https://stripe.com', '_blank')}
                            className="text-sm text-slate-500 hover:text-slate-900 underline underline-offset-4 decoration-1 font-serif"
                        >
                            Skip the line? Reserve Beta Access for $5
                        </button>
                    </div>

                </div>
            </motion.div>
        </div>
    );
};

export default LandingPage;
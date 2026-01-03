export default function PricingPage() {
  const plans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      features: [
        "100 AI responses per month",
        "Basic support",
        "Single content upload",
        "Email notifications"
      ],
      cta: "Start Free",
      highlighted: false
    },
    {
      name: "Starter",
      price: "$29",
      period: "per month",
      features: [
        "1,000 AI responses per month",
        "Unlimited content uploads",
        "Email support",
        "Custom widget styling",
        "Response analytics"
      ],
      cta: "Start Trial",
      highlighted: true
    },
    {
      name: "Pro",
      price: "$49",
      period: "per month",
      features: [
        "Unlimited AI responses",
        "Unlimited content uploads",
        "Priority support",
        "Custom widget styling",
        "Advanced analytics",
        "API access",
        "White-label option"
      ],
      cta: "Start Trial",
      highlighted: false
    }
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Choose the plan that works for your creator business. All plans include a 14-day free trial.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`rounded-lg p-8 ${
                plan.highlighted
                  ? "bg-indigo-600 text-white shadow-2xl transform scale-105"
                  : "bg-white text-gray-900 shadow-lg"
              }`}
            >
              {plan.highlighted && (
                <div className="text-center mb-4">
                  <span className="bg-white text-indigo-600 text-xs font-bold px-3 py-1 rounded-full">
                    MOST POPULAR
                  </span>
                </div>
              )}

              <div className="text-center mb-8">
                <h2
                  className={`text-2xl font-bold mb-2 ${
                    plan.highlighted ? "text-white" : "text-gray-900"
                  }`}
                >
                  {plan.name}
                </h2>
                <div className="flex items-baseline justify-center mb-2">
                  <span
                    className={`text-5xl font-bold ${
                      plan.highlighted ? "text-white" : "text-gray-900"
                    }`}
                  >
                    {plan.price}
                  </span>
                  <span
                    className={`ml-2 ${
                      plan.highlighted ? "text-indigo-200" : "text-gray-600"
                    }`}
                  >
                    {plan.period}
                  </span>
                </div>
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <svg
                      className={`w-5 h-5 mr-2 flex-shrink-0 mt-0.5 ${
                        plan.highlighted ? "text-indigo-200" : "text-green-500"
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span
                      className={
                        plan.highlighted ? "text-indigo-100" : "text-gray-600"
                      }
                    >
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <button
                className={`w-full py-3 px-6 rounded-lg font-semibold transition ${
                  plan.highlighted
                    ? "bg-white text-indigo-600 hover:bg-gray-100"
                    : "bg-indigo-600 text-white hover:bg-indigo-700"
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <p className="text-gray-600 mb-4">
            All plans include a 14-day free trial. No credit card required.
          </p>
          <p className="text-sm text-gray-500">
            Need a custom plan for your business?{" "}
            <a href="#" className="text-indigo-600 hover:underline">
              Contact us
            </a>
          </p>
        </div>
      </div>
    </main>
  );
}

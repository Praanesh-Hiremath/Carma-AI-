"use client";
import { useState, useRef, useEffect } from "react";

export default function Home() {
  const formRef = useRef(null);
  const newsRef = useRef(null);
  const resultsRef = useRef(null);
  const [scrolled, setScrolled] = useState(false);
  const [news, setNews] = useState([]);

  // States for Features
  const [heroSearch, setHeroSearch] = useState("");
  const [openPriceId, setOpenPriceId] = useState(null);
  const [leadModalOpen, setLeadModalOpen] = useState(false);
  const [selectedCarForLead, setSelectedCarForLead] = useState(null);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);

    // Crash-Proof News Fetch
    fetch("https://carma-ai-h8v9.onrender.com/recommend")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setNews(Array.isArray(data) ? data : []))
      .catch((err) => {
        console.error(err);
        setNews([]);
      });

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollTo = (ref) =>
    ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });

  const [formData, setFormData] = useState({
    budget: 2000000,
    seating_capacity: 5,
    fuel_types: [],
    body_types: [],
    priorities: [],
    specific_needs: "",
    search_query: "",
    state: "Delhi", // Default State
  });

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // --- LEAD GEN LOGIC ---
  const handleGetQuote = (carName) => {
    setSelectedCarForLead(carName);
    setLeadModalOpen(true);
  };

  const handleLeadSubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const leadData = {
      name: fd.get("name"),
      phone: fd.get("phone"),
      city: fd.get("city"),
      car_model: selectedCarForLead,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/submit-lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(leadData),
      });

      if (!response.ok) throw new Error("Failed");
      alert(
        `Success! A dealer for ${selectedCarForLead} will call you shortly.`
      );
      setLeadModalOpen(false);
    } catch (error) {
      alert("Error submitting details. Try again.");
    }
  };

  // --- SEARCH LOGIC ---
  const handleCheckbox = (category, value) => {
    setFormData((prev) => {
      const list = prev[category];
      if (list.includes(value))
        return { ...prev, [category]: list.filter((item) => item !== value) };
      return { ...prev, [category]: [...list, value] };
    });
  };

  const handleBudgetChange = (e) => {
    const rawValue = e.target.value;
    const numericString = rawValue.replace(/[^0-9]/g, "");
    const numericValue = numericString ? Number(numericString) : 0;
    setFormData({ ...formData, budget: numericValue });
  };

  const performSearch = async (overrideData = null) => {
    setLoading(true);
    setResults([]);
    const dataToSend = overrideData || formData;

    try {
      const response = await fetch("http://127.0.0.1:8000/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dataToSend),
      });

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setResults(Array.isArray(data) ? data : data.cars || []);

      if (
        (Array.isArray(data) && data.length > 0) ||
        (data.cars && data.cars.length > 0)
      ) {
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }, 300);
      }
    } catch (error) {
      alert("Backend Error: " + error.message);
    }
    setLoading(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    performSearch();
  };

  const handleHeroSearch = () => {
    if (!heroSearch.trim()) return;
    // Reset filters to give a clean search result
    const newData = {
      ...formData,
      search_query: heroSearch,
      fuel_types: [],
      body_types: [],
      specific_needs: "",
    };
    setFormData(newData);
    performSearch(newData);
  };

  const getSpecificNeedsList = () => {
    if (!formData.specific_needs) return [];
    return formData.specific_needs
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  };

  return (
    <div className="min-h-screen font-sans text-gray-900 bg-white selection:bg-black selection:text-white">
      {/* NAVBAR */}
      <nav
        className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? "bg-white shadow-md py-2" : "bg-black/80 backdrop-blur-md text-white py-4"}`}
      >
        <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
          <div className="flex items-center gap-8">
            <div
              className={`text-2xl font-extrabold tracking-tight ${scrolled ? "text-blue-600" : "text-white"}`}
            >
              Carma
            </div>
            <div
              className={`hidden md:flex space-x-6 text-sm font-medium ${scrolled ? "text-gray-600" : "text-gray-300"}`}
            >
              <button
                onClick={() => scrollTo(newsRef)}
                className="hover:text-blue-500 transition"
              >
                News & Reviews
              </button>
              <button
                onClick={() => scrollTo(formRef)}
                className="hover:text-blue-500 transition"
              >
                New Cars
              </button>
              <button
                onClick={() => scrollTo(formRef)}
                className="hover:text-blue-500 transition"
              >
                Compare
              </button>
            </div>
          </div>
          <button
            onClick={() => scrollTo(formRef)}
            className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-md text-sm font-bold transition shadow-lg"
          >
            Find My Car
          </button>
        </div>
      </nav>

      {/* HERO SECTION */}
      <div
        className="relative pt-48 pb-32 text-center px-6 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?q=80&w=2000&auto=format&fit=crop')",
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent"></div>
        <div className="relative max-w-4xl mx-auto z-10 text-white">
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            The Right Car, <br />{" "}
            <span className="text-blue-400">Right Now.</span>
          </h1>
          <p className="text-xl text-gray-300 mb-10 max-w-2xl mx-auto">
            India's most advanced AI car recommendation engine. Get on-road
            prices, hidden drawbacks, and vibe checks instantly.
          </p>

          <div className="bg-white p-2 rounded-full max-w-xl mx-auto flex shadow-2xl">
            <input
              type="text"
              placeholder="Search (e.g. Fortuner, Swift, SUV)"
              className="flex-1 rounded-l-full px-6 py-3 text-gray-800 outline-none font-medium"
              value={heroSearch}
              onChange={(e) => setHeroSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleHeroSearch()}
            />
            <button
              onClick={handleHeroSearch}
              className="bg-blue-600 text-white rounded-full px-8 py-3 font-bold hover:bg-blue-700 transition"
            >
              Search
            </button>
          </div>
        </div>
      </div>

      {/* AFFILIATE STRIP */}
      <div className="bg-gray-100 border-b border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-6 flex flex-wrap justify-center gap-6 text-sm font-medium text-gray-600">
          <a
            href="#"
            className="flex items-center gap-2 hover:text-blue-600 transition"
          >
            <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs font-bold">
              AD
            </span>{" "}
            Sell Your Car (Best Price) &rarr;
          </a>
          <a
            href="#"
            className="flex items-center gap-2 hover:text-blue-600 transition"
          >
            <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-bold">
              AD
            </span>{" "}
            Get Car Loan @ 8.5% &rarr;
          </a>
          <a
            href="#"
            className="flex items-center gap-2 hover:text-blue-600 transition"
          >
            <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs font-bold">
              AD
            </span>{" "}
            Buy Accessories &rarr;
          </a>
        </div>
      </div>

      {/* NEWS SECTION */}
      <div
        ref={newsRef}
        className="bg-white py-20 px-6 border-b border-gray-100"
      >
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-end mb-10">
            <h2 className="text-3xl font-bold text-gray-900">
              Latest Automotive News
            </h2>
            <a
              href="#"
              className="text-blue-600 font-bold text-sm hover:underline"
            >
              View All &rarr;
            </a>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {Array.isArray(news) &&
              news.map((item) => (
                <a
                  href={item.id}
                  target="_blank"
                  rel="noopener noreferrer"
                  key={item.id || Math.random()}
                  className="group cursor-pointer block"
                >
                  <div className="overflow-hidden rounded-xl mb-4 h-52 bg-gray-100">
                    <img
                      src={item.image}
                      alt="news"
                      className="w-full h-full object-cover transform group-hover:scale-105 transition duration-500"
                    />
                  </div>
                  <span className="text-xs font-bold text-red-500 uppercase tracking-wider">
                    {item.date}
                  </span>
                  <h3 className="text-xl font-bold mt-2 mb-2 group-hover:text-blue-600 transition">
                    {item.title}
                  </h3>
                  <p className="text-gray-500 text-sm line-clamp-2">
                    {item.snippet}
                  </p>
                </a>
              ))}
          </div>
        </div>
      </div>

      {/* MAIN TOOL SECTION */}
      <div ref={formRef} className="bg-gray-50 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
              AI Recommendation Engine
            </span>
            <h2 className="text-4xl font-bold tracking-tight mt-4 mb-3">
              Configure Your Needs
            </h2>
            <p className="text-gray-500">
              We analyze 50+ parameters to find your perfect match.
            </p>
          </div>

          <div className="bg-white p-8 md:p-12 rounded-3xl shadow-xl border border-gray-100">
            <form onSubmit={handleSubmit} className="space-y-12">
              {/* BUDGET & STATE SELECTOR */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                <div className="space-y-3">
                  <label className="text-sm font-bold uppercase text-gray-500 tracking-wider">
                    Budget
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-4 text-gray-400 text-xl font-serif">
                      ₹
                    </span>
                    <input
                      type="text"
                      className="w-full pl-10 p-4 bg-gray-50 border border-gray-200 rounded-xl text-2xl font-bold focus:ring-2 focus:ring-blue-500 outline-none transition"
                      value={
                        formData.budget
                          ? formData.budget.toLocaleString("en-IN")
                          : ""
                      }
                      onChange={handleBudgetChange}
                    />
                  </div>
                </div>
                <div className="space-y-3">
                  <label className="text-sm font-bold uppercase text-gray-500 tracking-wider">
                    Registration State
                  </label>
                  <select
                    className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl text-lg font-bold focus:ring-2 focus:ring-blue-500 outline-none"
                    value={formData.state}
                    onChange={(e) =>
                      setFormData({ ...formData, state: e.target.value })
                    }
                  >
                    <option value="Karnataka">Karnataka (High Tax)</option>
                    <option value="Delhi">Delhi (NCR)</option>
                    <option value="Maharashtra">Maharashtra</option>
                    <option value="Tamil Nadu">Tamil Nadu</option>
                    <option value="Other">Other State</option>
                  </select>
                </div>
              </div>

              {/* SEATING & FUEL */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                <div className="space-y-3">
                  <label className="text-sm font-bold uppercase text-gray-500 tracking-wider">
                    Seating
                  </label>
                  <div className="flex bg-gray-50 p-1.5 rounded-xl">
                    {[2, 5, 7].map((seat) => (
                      <button
                        key={seat}
                        type="button"
                        onClick={() =>
                          setFormData({ ...formData, seating_capacity: seat })
                        }
                        className={`flex-1 py-3 rounded-lg text-sm font-bold transition ${formData.seating_capacity === seat ? "bg-white shadow-md text-blue-600" : "text-gray-500 hover:text-gray-900"}`}
                      >
                        {seat === 2 ? "2 Seater" : seat + " Seater"}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-bold uppercase text-gray-500 tracking-wider mb-4 block">
                    Fuel Type
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {["Petrol", "Diesel", "Electric", "Hybrid"].map((fuel) => (
                      <label
                        key={fuel}
                        className={`px-4 py-2 rounded-lg border cursor-pointer transition-all text-sm font-medium ${formData.fuel_types.includes(fuel) ? "bg-green-50 border-green-500 text-green-700" : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"}`}
                      >
                        <input
                          type="checkbox"
                          className="hidden"
                          checked={formData.fuel_types.includes(fuel)}
                          onChange={() => handleCheckbox("fuel_types", fuel)}
                        />{" "}
                        {fuel}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* AI & BODY */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-2xl border border-blue-100">
                  <label className="flex items-center gap-2 text-sm font-bold uppercase text-purple-700 tracking-wider mb-3">
                    ✨ AI Specifics
                  </label>
                  <input
                    type="text"
                    placeholder="Describe your vibe: 'Macho', 'Boss Car', 'Zippy for city'"
                    className="w-full p-4 bg-white border border-blue-100 rounded-xl text-lg focus:ring-2 focus:ring-purple-500 outline-none placeholder:text-gray-300 shadow-sm"
                    value={formData.specific_needs}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        specific_needs: e.target.value,
                      })
                    }
                  />
                </div>
                <div>
                  <label className="text-sm font-bold uppercase text-gray-500 tracking-wider mb-4 block">
                    Body Style
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {["SUV", "Sedan", "Hatchback", "Coupe"].map((body) => (
                      <label
                        key={body}
                        className={`px-4 py-2 rounded-lg border cursor-pointer transition-all text-sm font-medium ${formData.body_types.includes(body) ? "bg-blue-50 border-blue-500 text-blue-700" : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"}`}
                      >
                        <input
                          type="checkbox"
                          className="hidden"
                          checked={formData.body_types.includes(body)}
                          onChange={() => handleCheckbox("body_types", body)}
                        />{" "}
                        {body}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-red-600 hover:bg-red-700 text-white text-xl font-bold py-5 rounded-xl shadow-xl hover:shadow-2xl transition-all transform active:scale-[0.99]"
              >
                {loading ? "Calculating Best Match..." : "Show Me Cars"}
              </button>
            </form>
          </div>
        </div>

        {/* RESULTS SECTION */}
        <div ref={resultsRef} className="max-w-7xl mx-auto mt-24 scroll-mt-24">
          
          {/* No Results Block */}
          {!loading && results.length === 0 && formData.search_query && (
            <div className="text-center py-20 bg-gray-50 rounded-2xl border border-dashed border-gray-300">
                <h3 className="text-2xl font-bold text-gray-400">No cars found for "{formData.search_query}"</h3>
                <p className="text-gray-500 mt-2">Try searching for generic terms like "SUV", "Sunroof", or "Petrol".</p>
                <button onClick={() => {
                    setHeroSearch("");
                    setFormData({...formData, search_query: ""});
                    performSearch({...formData, search_query: ""});
                }} className="mt-6 text-blue-600 font-bold hover:underline">Clear Search</button>
            </div>
          )}

          {!loading && results.length > 0 && (
            <div className="mb-10 flex items-end gap-4 border-b border-gray-200 pb-4">
              <h3 className="text-3xl font-bold text-gray-900">Search Results</h3>
              <span className="text-gray-500 mb-1.5">{results.length} cars found</span>
            </div>
          )}
          
          <div className="space-y-6">
            {results.map((item, index) => {
              const needsList = getSpecificNeedsList();
              const isPriceOpen = openPriceId === index;
              return (
                <div
                  key={index}
                  className="group bg-white rounded-2xl overflow-hidden shadow-sm border border-gray-200 hover:shadow-xl transition-all duration-300 flex flex-col md:flex-row"
                >
                  <div className="md:w-1/3 h-64 md:h-auto relative overflow-hidden">
                    <img
                      src={item.car_details.image}
                      alt={item.car_details.model}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-3 left-3 bg-white/90 backdrop-blur px-3 py-1 text-xs font-bold rounded-md shadow-sm">
                      {item.match_score}% Match
                    </div>
                  </div>
                  <div className="md:w-2/3 p-6 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900">
                            {item.car_details.model}
                          </h2>
                          <p className="text-gray-500 text-sm font-medium">
                            {item.car_details.make} •{" "}
                            {item.car_details.body_type} •{" "}
                            {item.car_details.fuel_type}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-gray-900">
                            {item.car_details.ex_showroom_price}
                          </p>
                          <p className="text-xs text-gray-500">Ex-Showroom</p>
                        </div>
                      </div>
                      {item.ai_notes.length > 0 && (
                        <div className="bg-purple-50 text-purple-800 text-sm p-3 rounded-lg mb-4">
                          <strong>AI Insight:</strong> {item.ai_notes.join(" ")}
                        </div>
                      )}
                      {item.cons.length > 0 && (
                        <div className="flex flex-wrap gap-x-4 gap-y-1 mb-4">
                          {item.cons.map((con, i) => (
                            <span
                              key={i}
                              className="text-xs text-red-600 flex items-center gap-1 font-medium"
                            >
                              • {con}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="grid grid-cols-3 gap-4 border-t border-b border-gray-100 py-4 my-2 text-sm text-gray-600">
                        <div>
                          <span className="block text-gray-400 text-xs uppercase">
                            Mileage
                          </span>
                          <span className="font-bold text-gray-800">
                            {item.car_details.mileage}
                          </span>
                        </div>
                        <div>
                          <span className="block text-gray-400 text-xs uppercase">
                            Power
                          </span>
                          <span className="font-bold text-gray-800">
                            {item.car_details.horsepower}
                          </span>
                        </div>
                        <div>
                          <span className="block text-gray-400 text-xs uppercase">
                            Safety
                          </span>
                          <span className="font-bold text-gray-800">
                            {item.car_details.safety_rating}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-3">
                      <button
                        onClick={() =>
                          setOpenPriceId(isPriceOpen ? null : index)
                        }
                        className="flex-1 bg-white border border-gray-300 text-gray-700 py-2.5 rounded-lg font-bold hover:bg-gray-50 transition"
                      >
                        {isPriceOpen
                          ? "Hide Price Breakdown"
                          : "Check On-Road Price"}
                      </button>
                      <button
                        onClick={() => handleGetQuote(item.car_details.model)}
                        className="flex-1 bg-red-600 text-white py-2.5 rounded-lg font-bold hover:bg-red-700 transition"
                      >
                        Get Dealer Quote
                      </button>
                    </div>
                    {isPriceOpen && (
                      <div className="mt-4 bg-gray-50 p-4 rounded-lg border border-gray-200 animate-fade-in">
                        <h4 className="font-bold text-gray-900 mb-3 text-sm">
                          On-Road Price Breakdown (Est.)
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Ex-Showroom</span>
                            <span className="font-medium">
                              {item.car_details.on_road_price.ex_showroom}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">
                              RTO ({formData.state})
                            </span>
                            <span className="font-medium">
                              {item.car_details.on_road_price.rto}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Insurance</span>
                            <span className="font-medium">
                              {item.car_details.on_road_price.insurance}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">TCS (1%)</span>
                            <span className="font-medium">
                              {item.car_details.on_road_price.tcs}
                            </span>
                          </div>
                          <div className="flex justify-between pt-2 border-t border-gray-300 mt-2">
                            <span className="font-bold text-gray-900">
                              Total
                            </span>
                            <span className="font-bold text-red-600 text-lg">
                              {item.car_details.on_road_price.total}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* LEAD MODAL */}
      {leadModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative">
            <button
              onClick={() => setLeadModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-black"
            >
              ✕
            </button>
            <h3 className="text-2xl font-bold mb-2">Get Best Offer</h3>
            <p className="text-gray-500 mb-6 text-sm">
              Get the best on-road price for{" "}
              <span className="font-bold text-black">{selectedCarForLead}</span>{" "}
              from dealers near you.
            </p>
            <form onSubmit={handleLeadSubmit} className="space-y-4">
              <input
                name="name"
                type="text"
                placeholder="Your Name"
                className="w-full p-3 border rounded-lg outline-none focus:border-red-500"
                required
              />
              <input
                name="phone"
                type="tel"
                placeholder="Mobile Number"
                className="w-full p-3 border rounded-lg outline-none focus:border-red-500"
                required
              />
              <input
                name="city"
                type="text"
                placeholder="City"
                className="w-full p-3 border rounded-lg outline-none focus:border-red-500"
                required
              />
              <button
                type="submit"
                className="w-full bg-red-600 text-white font-bold py-3 rounded-lg hover:bg-red-700 transition"
              >
                Request Call Back
              </button>
            </form>
            <p className="text-[10px] text-gray-400 mt-4 text-center">
              By submitting, you agree to receive calls from partners.
            </p>
          </div>
        </div>
      )}

      {/* FOOTER */}
      <footer className="bg-gray-900 text-white py-12 text-center mt-20">
        <div className="text-2xl font-extrabold tracking-tight mb-4">Carma</div>
        <p className="text-gray-400 text-sm">
          © 2025 Carma India. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
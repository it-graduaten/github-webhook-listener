module.exports = {
  content: ["./src/*.html"],
  theme: {
    extend: {
      colors: {
        "daily-dev-tips": "#F89283",
      },
    },
  },
  variants: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["corporate", "business"],
    darkTheme: "business",
    lightTheme: "corporate",
  },
};

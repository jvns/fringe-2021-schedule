const app = Vue.createApp({
  async mounted() {
    this.readHash();
    window.addEventListener(
      "hashchange",
      () => {
        console.log("hashchange");
        this.readHash();
      },
      false,
    );
    // get language from local storage if possible
    const language = localStorage.getItem("language");
    if (language) {
      this.language = language;
    }
    // get performances-2024.json
    const json = await fetch("performances-2024.json");
    const performances = await json.json();
    // map title to performance
    for (const performance of performances) {
      if (performance.performances.dates.length == 0) {
        continue;
      }
      this.performances[performance.title] = performance;
    }
  },
  data() {
    return {
      performances: {},
      titles: [],
      hoveredShow: undefined,
      language: "en",
    };
  },
  // put titles in hash when they change
  watch: {
    titles() {
      const hash = this.titles.join("::");
      window.location.hash = hash;
    },
    language() {
      localStorage.setItem("language", this.language);
    },
  },
  computed: {
    english() {
      return this.language === "en";
    },
  },
  methods: {
    readHash() {
      const hash = decodeURIComponent(window.location.hash.slice(1));
      if (hash) {
        this.titles = hash.split("::");
      } else {
        this.titles = [];
      }
    },
    performanceTitles() {
      const titles = Object.keys(this.performances);
      //sort, ignore case
      titles.sort((a, b) =>
        a.localeCompare(b, undefined, { sensitivity: "base" }),
      );
      return titles;
    },
    testMethod() {
      return "hello!";
    },
    formatDate(date) {
      // translate 07/06/2024 to 'June 7'
      const [day, month, year] = date.split("/");
      return parseInt(day);
    },
    fringeShows(day) {
      const shows = [];
      for (const title of this.titles) {
        const performance = this.performances[title];
        if (!performance) {
          continue;
        }
        if (performance.performances.dates.includes(day)) {
          shows.push(performance);
        }
      }
      // sort shows by time
      shows.sort((a, b) => {
        const timeA = a.performances.times[day][0].performanceTime;
        const timeB = b.performances.times[day][0].performanceTime;
        return timeA < timeB ? -1 : 1;
      });
      return shows;
    },
    fringeDates() {
      return [
        "03/06/2024",
        "04/06/2024",
        "05/06/2024",
        "06/06/2024",
        "07/06/2024",
        "08/06/2024",
        "09/06/2024",
        "10/06/2024",
        "11/06/2024",
        "12/06/2024",
        "13/06/2024",
        "14/06/2024",
        "15/06/2024",
        "16/06/2024",
        "17/06/2024",
        "18/06/2024",
        "19/06/2024",
        "20/06/2024",
      ];
    },
  },
});
app.component("vue-multiselect", window["vue-multiselect"].default);
app.mount("#app");

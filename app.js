const quickMap = {
  AA: ["日", "曰", "口"],
  AB: ["月", "用"],
  AC: ["木", "本", "未"],
  AD: ["水", "永"],
  AE: ["火", "灬"],
  AF: ["土", "士"],
  AG: ["金", "針"],
  AH: ["竹", "箱"],
  AJ: ["人", "今"],
  AK: ["心", "必"],
  AL: ["女", "好"],
  AM: ["田", "由"],
  AN: ["山", "岑"],
  AO: ["一", "丁"],
  AP: ["弓", "強"],
  AQ: ["言", "記"],
  AR: ["手", "打"],
  AS: ["大", "太"],
  AT: ["犬", "狀"],
  AU: ["馬", "駐"],
  AV: ["王", "主"],
  AW: ["雨", "雪"],
  AX: ["門", "問"],
  AY: ["心", "思"],
  AZ: ["子", "孫"],
  KM: ["速", "成"],
  KL: ["輸", "輸"],
  KJ: ["入", "來"],
  QQ: ["語", "說"],
  QW: ["讀", "談"],
  RM: ["打", "托"],
  RT: ["掌", "握"],
  SA: ["大", "天"],
  SH: ["幫", "助"],
  ZX: ["學", "習"],
};

const referenceList = [
  { code: "AA", word: "日" },
  { code: "AB", word: "月" },
  { code: "AC", word: "木" },
  { code: "AD", word: "水" },
  { code: "AE", word: "火" },
  { code: "AF", word: "土" },
  { code: "AG", word: "金" },
  { code: "AH", word: "竹" },
  { code: "AJ", word: "人" },
  { code: "AL", word: "女" },
  { code: "AM", word: "田" },
  { code: "AN", word: "山" },
  { code: "AO", word: "一" },
  { code: "AQ", word: "言" },
  { code: "AR", word: "手" },
  { code: "AS", word: "大" },
  { code: "AT", word: "犬" },
  { code: "AU", word: "馬" },
  { code: "AV", word: "王" },
  { code: "AW", word: "雨" },
  { code: "AX", word: "門" },
  { code: "AZ", word: "子" },
  { code: "KM", word: "速" },
  { code: "QQ", word: "語" },
  { code: "ZX", word: "學" },
];

const codeInput = document.getElementById("codeInput");
const candidateList = document.getElementById("candidateList");
const matchHint = document.getElementById("matchHint");
const output = document.getElementById("output");
const clearOutput = document.getElementById("clearOutput");
const referenceListEl = document.getElementById("referenceList");
const toggleSize = document.getElementById("toggleSize");

let isLarge = false;

const renderReference = () => {
  referenceListEl.innerHTML = referenceList
    .map((item) => `<li><strong>${item.code}</strong> → ${item.word}</li>`)
    .join("");
};

const renderCandidates = (items, query) => {
  candidateList.innerHTML = "";

  if (!query) {
    matchHint.textContent = "請輸入 1～4 碼查詢。";
    return;
  }

  if (!items.length) {
    matchHint.textContent = `沒有找到「${query}」的候選字。`;
    return;
  }

  matchHint.textContent = `找到 ${items.length} 個候選字：`;

  items.forEach((word) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "candidate";
    button.textContent = word;
    button.addEventListener("click", () => {
      output.value += word;
      codeInput.focus();
    });
    candidateList.appendChild(button);
  });
};

const handleInput = () => {
  const query = codeInput.value.trim().toUpperCase();
  const exactMatches = quickMap[query] ?? [];

  if (exactMatches.length) {
    renderCandidates(exactMatches, query);
    return;
  }

  const partialMatches = Object.entries(quickMap)
    .filter(([code]) => code.startsWith(query) && query.length > 0)
    .flatMap(([, words]) => words)
    .slice(0, 12);

  renderCandidates(partialMatches, query);
};

const updateSizeToggle = () => {
  candidateList.classList.toggle("is-large", isLarge);
  toggleSize.textContent = isLarge ? "縮小選字表" : "放大選字表";
};

codeInput.addEventListener("input", handleInput);
clearOutput.addEventListener("click", () => {
  output.value = "";
});
toggleSize.addEventListener("click", () => {
  isLarge = !isLarge;
  updateSizeToggle();
});

renderReference();
renderCandidates([], "");
updateSizeToggle();

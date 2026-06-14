// Auto-save van de voorraad-aantallen: elke wijziging (pijltjes of typen) bewaart vanzelf.
document.querySelectorAll(".stock-input").forEach(function (inp) {
  inp.addEventListener("change", function () {
    var podId = inp.dataset.pod;
    var body = new URLSearchParams({ pod_id: podId, stock: inp.value });
    fetch("/admin/stock", { method: "POST", body: body })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !data.ok) return;
        var row = inp.closest("tr");
        var left = row.querySelector(".left-cell");
        if (left) left.textContent = data.remaining;
        inp.classList.add("saved");
        setTimeout(function () { inp.classList.remove("saved"); }, 700);
      })
      .catch(function () {});
  });
});

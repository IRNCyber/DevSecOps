(() => {
  const dialog = document.querySelector("#task-dialog");
  const form = document.querySelector("#task-form");
  const list = document.querySelector("#task-list");
  const empty = document.querySelector("#empty-state");
  const toast = document.querySelector("#toast");
  const search = document.querySelector("#search");
  let activeFilter = "all";
  let editingId = null;
  let searchTimer = null;
  let toastTimer = null;

  const labels = { all: "All tasks", open: "To do", in_progress: "In progress", done: "Completed" };
  const dateFormatter = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" });

  function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("show"), 2800);
  }

  async function api(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
    });
    if (response.status === 204) return null;
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
    return data;
  }

  function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function formatDate(value) {
    if (!value) return "No due date";
    const date = new Date(`${value}T00:00:00`);
    return dateFormatter.format(date);
  }

  function buildTask(task) {
    const row = createElement("article", `task-row${task.status === "done" ? " completed" : ""}`);
    const main = createElement("div", "task-main");
    const check = createElement("button", `task-check${task.status === "done" ? " is-done" : ""}`, task.status === "done" ? "✓" : "");
    check.type = "button";
    check.setAttribute("aria-label", task.status === "done" ? `Reopen ${task.title}` : `Complete ${task.title}`);
    check.addEventListener("click", () => changeStatus(task, task.status === "done" ? "open" : "done"));

    const text = createElement("div", "task-text");
    text.append(createElement("div", "task-title", task.title));
    if (task.description) text.append(createElement("div", "task-description", task.description));
    main.append(check, text);

    const priority = createElement("span", `priority priority-${task.priority}`, task.priority[0].toUpperCase() + task.priority.slice(1));
    const status = createElement("span", `status-pill status-${task.status}`, labels[task.status]);
    const due = createElement("time", "due-date", formatDate(task.due_date));
    if (task.due_date) {
      due.dateTime = task.due_date;
      if (task.status !== "done" && task.due_date < new Date().toISOString().slice(0, 10)) due.classList.add("overdue");
    }

    const actions = createElement("div", "row-actions");
    const edit = createElement("button", "row-action", "···");
    edit.type = "button";
    edit.setAttribute("aria-label", `Edit ${task.title}`);
    edit.title = "Edit task";
    edit.addEventListener("click", () => openEditor(task));
    const remove = createElement("button", "row-action", "×");
    remove.type = "button";
    remove.setAttribute("aria-label", `Delete ${task.title}`);
    remove.title = "Delete task";
    remove.addEventListener("click", () => deleteTask(task));
    actions.append(edit, remove);
    row.append(main, priority, status, due, actions);
    return row;
  }

  async function loadTasks() {
    list.setAttribute("aria-busy", "true");
    const params = new URLSearchParams();
    if (activeFilter !== "all") params.set("status", activeFilter);
    if (search.value.trim()) params.set("q", search.value.trim());
    try {
      const result = await api(`/api/tasks?${params.toString()}`);
      const fragment = document.createDocumentFragment();
      result.tasks.forEach((task) => fragment.append(buildTask(task)));
      list.replaceChildren(fragment);
      document.querySelector("#stat-total").textContent = result.stats.total;
      document.querySelector("#stat-open").textContent = result.stats.open;
      document.querySelector("#stat-progress").textContent = result.stats.in_progress;
      document.querySelector("#stat-done").textContent = result.stats.done;
      document.querySelector("#nav-total").textContent = result.stats.total;
      document.querySelector("#nav-open").textContent = result.stats.open;
      document.querySelector("#nav-progress").textContent = result.stats.in_progress;
      document.querySelector("#nav-done").textContent = result.stats.done;
      document.querySelector("#task-count").textContent = `${result.tasks.length} ${result.tasks.length === 1 ? "task" : "tasks"}${search.value.trim() ? " found" : " shown"}`;
      const noTasks = result.tasks.length === 0;
      empty.hidden = !noTasks;
      document.querySelector("#empty-title").textContent = search.value.trim() ? "No matches yet." : activeFilter === "done" ? "Nothing completed yet." : "A little room to think.";
      document.querySelector("#empty-copy").textContent = search.value.trim() ? "Try a different search, or clear the search field." : "Your task list is clear. Add a task to get started.";
      document.querySelector("#empty-add").hidden = Boolean(search.value.trim()) || activeFilter === "done";
    } catch (error) {
      list.replaceChildren();
      empty.hidden = false;
      document.querySelector("#empty-title").textContent = "Could not load your tasks.";
      document.querySelector("#empty-copy").textContent = error.message;
      document.querySelector("#empty-add").hidden = true;
    } finally {
      list.removeAttribute("aria-busy");
    }
  }

  async function changeStatus(task, status) {
    try {
      await api(`/api/tasks/${task.id}`, { method: "PATCH", body: JSON.stringify({ status }) });
      await loadTasks();
      showToast(status === "done" ? "Task completed." : "Task moved back to to do.");
    } catch (error) {
      showToast(error.message, true);
    }
  }

  async function deleteTask(task) {
    if (!window.confirm(`Delete “${task.title}”? This cannot be undone.`)) return;
    try {
      await api(`/api/tasks/${task.id}`, { method: "DELETE" });
      await loadTasks();
      showToast("Task deleted.");
    } catch (error) {
      showToast(error.message, true);
    }
  }

  function openEditor(task = null) {
    editingId = task ? task.id : null;
    form.reset();
    document.querySelector("#dialog-title").textContent = task ? "Edit task" : "Create a task";
    document.querySelector("#save-task").textContent = task ? "Save changes" : "Save task";
    document.querySelector("#title").value = task?.title || "";
    document.querySelector("#description").value = task?.description || "";
    document.querySelector("#priority").value = task?.priority || "medium";
    document.querySelector("#status").value = task?.status || "open";
    document.querySelector("#due-date").value = task?.due_date || "";
    document.querySelector("#form-error").hidden = true;
    dialog.showModal();
    document.querySelector("#title").focus();
  }

  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.filter;
      document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item === button));
      document.querySelector("#view-name").textContent = labels[activeFilter];
      document.querySelector("#heading-title").firstChild.textContent = labels[activeFilter];
      loadTasks();
    });
  });

  document.querySelector("#add-task").addEventListener("click", () => openEditor());
  document.querySelector("#empty-add").addEventListener("click", () => openEditor());
  document.querySelector("#close-dialog").addEventListener("click", () => dialog.close());
  document.querySelector("#cancel-dialog").addEventListener("click", () => dialog.close());
  search.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(loadTasks, 180);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const save = document.querySelector("#save-task");
    const errorBox = document.querySelector("#form-error");
    const data = Object.fromEntries(new FormData(form).entries());
    if (!data.due_date) data.due_date = null;
    save.disabled = true;
    errorBox.hidden = true;
    try {
      await api(editingId ? `/api/tasks/${editingId}` : "/api/tasks", {
        method: editingId ? "PATCH" : "POST",
        body: JSON.stringify(data),
      });
      dialog.close();
      await loadTasks();
      showToast(editingId ? "Changes saved." : "Task created.");
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
    } finally {
      save.disabled = false;
    }
  });

  document.querySelector("#today-label").textContent = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" }).format(new Date()).toUpperCase();
  loadTasks();
})();

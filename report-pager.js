(function () {
  const SCREEN_PAGINATION_MIN_WIDTH = 900;
  let resizeTimer = null;

  function getSourceArticle() {
    return document.querySelector("main > article.chapter-source, main > article");
  }

  function clearRenderedPages(main) {
    const existing = main.querySelector(".page-stack");
    if (existing) {
      existing.remove();
    }
  }

  function shouldPaginate() {
    return window.innerWidth > SCREEN_PAGINATION_MIN_WIDTH;
  }

  function createPage(titleText) {
    const page = document.createElement("section");
    page.className = "report-page";

    const content = document.createElement("div");
    content.className = "report-page__content";

    const footer = document.createElement("div");
    footer.className = "report-page__footer";

    const title = document.createElement("span");
    title.textContent = titleText;

    const number = document.createElement("span");
    number.textContent = "";

    footer.appendChild(title);
    footer.appendChild(number);
    page.appendChild(content);
    page.appendChild(footer);

    return { page, content, title, number };
  }

  function buildState(main, titleText) {
    const stack = document.createElement("div");
    stack.className = "page-stack";
    main.appendChild(stack);

    const state = {
      main,
      stack,
      pages: [],
      currentPage: null,
      titleText
    };

    newPage(state);
    return state;
  }

  function newPage(state) {
    const page = createPage(state.titleText);
    state.stack.appendChild(page.page);
    state.pages.push(page);
    state.currentPage = page;
    return page;
  }

  function hasOverflow(pageContent) {
    return Math.ceil(pageContent.scrollHeight) > Math.ceil(pageContent.clientHeight + 1);
  }

  function shouldBreakBefore(node) {
    return (
      node &&
      node.nodeType === Node.ELEMENT_NODE &&
      (node.classList.contains("page-break-before") ||
        node.getAttribute("data-force-page-break") === "before")
    );
  }

  function isPageEmpty(page) {
    return page.content.children.length === 0;
  }

  function appendAndCheck(page, node) {
    page.content.appendChild(node);
    if (hasOverflow(page.content)) {
      page.content.removeChild(node);
      return false;
    }
    return true;
  }

  function appendChildToFragment(page, fragment, child) {
    fragment.appendChild(child);
    if (hasOverflow(page.content)) {
      fragment.removeChild(child);
      return false;
    }
    return true;
  }

  function getRenderableChildren(node) {
    return Array.from(node.childNodes).filter((child) => {
      if (child.nodeType === Node.ELEMENT_NODE) {
        return true;
      }

      return child.nodeType === Node.TEXT_NODE && child.textContent.trim().length > 0;
    });
  }

  function isHeadingTagName(tagName) {
    return /^H[1-6]$/.test(tagName);
  }

  function isHeadingNode(node) {
    return node.nodeType === Node.ELEMENT_NODE && isHeadingTagName(node.tagName);
  }

  function canFitInPage(page, node) {
    page.content.appendChild(node);
    const fits = !hasOverflow(page.content);
    page.content.removeChild(node);
    return fits;
  }

  function cloneHeading(heading, isContinuation) {
    if (!heading) {
      return null;
    }

    const clone = heading.cloneNode(true);
    if (isContinuation) {
      clone.classList.add("continued-heading");
    }
    return clone;
  }

  function createSectionFragment(section, heading, isContinuation) {
    const fragment = section.cloneNode(false);
    const headingClone = cloneHeading(heading, isContinuation);

    if (headingClone) {
      fragment.appendChild(headingClone);
    }

    return fragment;
  }

  function getFragmentBodyCount(fragment) {
    return Array.from(fragment.childNodes).filter((child) => {
      if (child.nodeType === Node.TEXT_NODE) {
        return child.textContent.trim().length > 0;
      }

      return !isHeadingNode(child);
    }).length;
  }

  function startSectionFragment(section, heading, isContinuation, state, firstChild) {
    let page = state.currentPage;

    if (!isPageEmpty(page) && firstChild) {
      const probe = createSectionFragment(section, heading, isContinuation);
      probe.appendChild(firstChild.cloneNode(true));

      if (!canFitInPage(page, probe)) {
        page = newPage(state);
        state.currentPage = page;
      }
    }

    let fragment = createSectionFragment(section, heading, isContinuation);

    if (!appendAndCheck(state.currentPage, fragment)) {
      if (!isPageEmpty(state.currentPage)) {
        page = newPage(state);
        state.currentPage = page;
        fragment = createSectionFragment(section, heading, isContinuation);
        appendAndCheck(state.currentPage, fragment);
      } else {
        state.currentPage.content.appendChild(fragment);
      }
    }

    return fragment;
  }

  function createTableSkeleton(table) {
    const tableClone = table.cloneNode(false);
    const thead = table.querySelector("thead");
    const tbody = document.createElement("tbody");

    if (thead) {
      tableClone.appendChild(thead.cloneNode(true));
    }

    tableClone.appendChild(tbody);
    return tableClone;
  }

  function getTableRows(table) {
    const bodyRows = Array.from(table.querySelectorAll("tbody > tr"));
    if (bodyRows.length > 0) {
      return bodyRows;
    }

    const allRows = Array.from(table.querySelectorAll("tr"));
    if (table.querySelector("thead") && allRows.length > 0) {
      return allRows.slice(1);
    }

    return allRows;
  }

  function splitTableIntoSection(section, heading, fragment, table, continuationUsed, state) {
    let page = state.currentPage;
    let currentFragment = fragment;
    let isContinuation = continuationUsed;
    let tableFragment = createTableSkeleton(table);

    if (!appendChildToFragment(page, currentFragment, tableFragment)) {
      if (getFragmentBodyCount(currentFragment) > 0) {
        page = newPage(state);
        state.currentPage = page;
        currentFragment = startSectionFragment(section, heading, true, state, table);
        isContinuation = true;
        tableFragment = createTableSkeleton(table);
        appendChildToFragment(page, currentFragment, tableFragment);
      } else {
        currentFragment.appendChild(tableFragment);
      }
    }

    const rows = getTableRows(table);
    let tbody = tableFragment.querySelector("tbody");

    rows.forEach((row) => {
      const rowClone = row.cloneNode(true);
      tbody.appendChild(rowClone);

      if (hasOverflow(page.content)) {
        tbody.removeChild(rowClone);

        if (tbody.children.length === 0) {
          tbody.appendChild(rowClone);
          return;
        }

        page = newPage(state);
        state.currentPage = page;
        currentFragment = startSectionFragment(section, heading, true, state, table);
        isContinuation = true;
        tableFragment = createTableSkeleton(table);
        appendChildToFragment(page, currentFragment, tableFragment);
        tbody = tableFragment.querySelector("tbody");
        tbody.appendChild(rowClone);
      }
    });

    return { fragment: currentFragment, isContinuation };
  }

  function splitListIntoSection(section, heading, fragment, list, continuationUsed, state) {
    let page = state.currentPage;
    let currentFragment = fragment;
    let isContinuation = continuationUsed;
    let listFragment = list.cloneNode(false);

    if (!appendChildToFragment(page, currentFragment, listFragment)) {
      if (getFragmentBodyCount(currentFragment) > 0) {
        page = newPage(state);
        state.currentPage = page;
        currentFragment = startSectionFragment(section, heading, true, state, list);
        isContinuation = true;
        listFragment = list.cloneNode(false);
        appendChildToFragment(page, currentFragment, listFragment);
      } else {
        currentFragment.appendChild(listFragment);
      }
    }

    const items = Array.from(list.children);
    items.forEach((item) => {
      const itemClone = item.cloneNode(true);
      listFragment.appendChild(itemClone);

      if (hasOverflow(page.content)) {
        listFragment.removeChild(itemClone);

        if (listFragment.children.length === 0) {
          listFragment.appendChild(itemClone);
          return;
        }

        page = newPage(state);
        state.currentPage = page;
        currentFragment = startSectionFragment(section, heading, true, state, list);
        isContinuation = true;
        listFragment = list.cloneNode(false);
        appendChildToFragment(page, currentFragment, listFragment);
        listFragment.appendChild(itemClone);
      }
    });

    return { fragment: currentFragment, isContinuation };
  }

  function splitSection(section, state) {
    const children = getRenderableChildren(section);
    const firstElement = children.find((child) => child.nodeType === Node.ELEMENT_NODE);
    const hasHeading = firstElement && isHeadingTagName(firstElement.tagName);
    const heading = hasHeading ? firstElement : null;
    const bodyChildren = heading ? children.slice(1) : children.slice();
    let fragment = null;
    let isContinuation = false;

    if (bodyChildren.length === 0) {
      startSectionFragment(section, heading, false, state, null);
      return;
    }

    bodyChildren.forEach((child) => {
      if (!fragment) {
        fragment = startSectionFragment(section, heading, isContinuation, state, child);
      }

      let childClone = child.cloneNode(true);
      if (appendChildToFragment(state.currentPage, fragment, childClone)) {
        return;
      }

      const hasBodyContent = getFragmentBodyCount(fragment) > 0;
      if (hasBodyContent) {
        newPage(state);
        isContinuation = true;
        fragment = startSectionFragment(section, heading, true, state, child);
        childClone = child.cloneNode(true);
        isContinuation = true;

        if (appendChildToFragment(state.currentPage, fragment, childClone)) {
          return;
        }
      }

      if (child.nodeType === Node.ELEMENT_NODE && child.tagName === "TABLE") {
        const result = splitTableIntoSection(section, heading, fragment, child, isContinuation, state);
        fragment = result.fragment;
        isContinuation = result.isContinuation;
        return;
      }

      if (child.nodeType === Node.ELEMENT_NODE && (child.tagName === "UL" || child.tagName === "OL")) {
        const result = splitListIntoSection(section, heading, fragment, child, isContinuation, state);
        fragment = result.fragment;
        isContinuation = result.isContinuation;
        return;
      }

      fragment.appendChild(childClone);
    });
  }

  function placeBlock(state, block) {
    if (shouldBreakBefore(block) && !isPageEmpty(state.currentPage)) {
      newPage(state);
    }

    const clone = block.cloneNode(true);

    if (appendAndCheck(state.currentPage, clone)) {
      return;
    }

    if (!isPageEmpty(state.currentPage)) {
      newPage(state);
      if (appendAndCheck(state.currentPage, clone)) {
        return;
      }
    }

    if (block.nodeType === Node.ELEMENT_NODE && block.tagName === "SECTION") {
      splitSection(block, state);
      return;
    }

    if (block.nodeType === Node.ELEMENT_NODE && block.tagName === "HEADER") {
      splitSection(block, state);
      return;
    }

    state.currentPage.content.appendChild(clone);
  }

  function elementHasMeaningfulContent(node) {
    if (!node) {
      return false;
    }

    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent.trim().length > 0;
    }

    if (node.nodeType !== Node.ELEMENT_NODE) {
      return false;
    }

    if (isHeadingNode(node)) {
      return node.textContent.trim().length > 0;
    }

    if (node.matches("table")) {
      return getTableRows(node).length > 0;
    }

    if (node.matches("ul, ol")) {
      return node.children.length > 0;
    }

    if (node.matches(".visual, img, svg")) {
      return true;
    }

    const meaningfulChildren = Array.from(node.childNodes).filter((child) => {
      if (child.nodeType === Node.TEXT_NODE) {
        return child.textContent.trim().length > 0;
      }

      if (child.nodeType !== Node.ELEMENT_NODE) {
        return false;
      }

      if (isHeadingNode(child)) {
        return false;
      }

      return elementHasMeaningfulContent(child);
    });

    if (meaningfulChildren.length > 0) {
      return true;
    }

    const ownText = Array.from(node.childNodes)
      .filter((child) => child.nodeType === Node.TEXT_NODE)
      .map((child) => child.textContent)
      .join("")
      .replace(/\s+/g, "");

    return ownText.length > 0;
  }

  function pruneMeaninglessChildren(root) {
    Array.from(root.children).forEach((child) => {
      pruneMeaninglessChildren(child);

      if (!elementHasMeaningfulContent(child)) {
        child.remove();
      }
    });
  }

  function cleanupPages(state) {
    state.pages = state.pages.filter((page) => {
      pruneMeaninglessChildren(page.content);

      if (!elementHasMeaningfulContent(page.content)) {
        page.page.remove();
        return false;
      }

      return true;
    });
  }

  function renumberPages(state) {
    state.pages.forEach((page, index) => {
      page.number.textContent = "Page " + (index + 1);
    });
  }

  function buildTargetPageMap(state) {
    const pageMap = new Map();

    state.pages.forEach((page, index) => {
      page.content.querySelectorAll("[id]").forEach((node) => {
        if (!pageMap.has(node.id)) {
          pageMap.set(node.id, index + 1);
        }
      });
    });

    return pageMap;
  }

  function populateTocTargets(state) {
    const pageMap = buildTargetPageMap(state);

    state.stack.querySelectorAll("[data-toc-target]").forEach((node) => {
      const target = node.getAttribute("data-toc-target");
      const pageNumber = pageMap.get(target);

      if (pageNumber) {
        node.textContent = String(pageNumber);
      }
    });
  }

  function renderPages() {
    const source = getSourceArticle();
    if (!source) {
      return;
    }

    source.classList.add("chapter-source");

    const main = source.parentElement;
    clearRenderedPages(main);
    document.body.classList.remove("is-paginated");

    if (!shouldPaginate()) {
      return;
    }

    const titleText =
      source.getAttribute("data-running-title") ||
      (source.querySelector("h1") || {}).textContent ||
      document.title;
    const state = buildState(main, titleText.trim());
    const blocks = getRenderableChildren(source);

    blocks.forEach((block) => {
      placeBlock(state, block);
    });

    cleanupPages(state);
    renumberPages(state);
    populateTocTargets(state);
    document.body.classList.add("is-paginated");
  }

  function scheduleRender() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(renderPages, 120);
  }

  document.addEventListener("DOMContentLoaded", renderPages);
  window.addEventListener("load", renderPages);
  window.addEventListener("resize", scheduleRender);

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(renderPages).catch(function () {
      renderPages();
    });
  }
})();

(function () {
  "use strict";

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : null;
  }

  function getCsrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    return (input && input.value) || getCookie("csrftoken") || "";
  }

  function setStatus(widget, message, isError) {
    const status = widget.querySelector(".s3-file-status");
    if (!status) {
      return;
    }
    status.textContent = message;
    status.classList.toggle("s3-file-status-error", Boolean(isError));
  }

  function setProgress(widget, percent) {
    const progress = widget.querySelector(".s3-file-progress");
    if (!progress) {
      return;
    }
    progress.hidden = false;
    progress.value = Math.min(100, Math.max(0, percent));
  }

  function resetProgress(widget) {
    const progress = widget.querySelector(".s3-file-progress");
    if (!progress) {
      return;
    }
    progress.hidden = true;
    progress.value = 0;
  }

  function updateCurrentFile(widget, path) {
    const hidden = widget.querySelector(".s3-file-path-input");
    if (hidden) {
      hidden.value = path || "";
    }

    let current = widget.querySelector(".s3-file-current");
    if (path) {
      const name = path.split("/").pop();
      if (!current) {
        current = document.createElement("p");
        current.className = "s3-file-current";
        current.innerHTML =
          'Current: <span class="s3-file-current-name"></span> ' +
          '<button type="button" class="s3-file-clear-button">Clear</button>';
        const picker = widget.querySelector(".s3-file-picker");
        widget.insertBefore(current, picker);
      }
      const nameEl = current.querySelector(".s3-file-current-name");
      if (nameEl) {
        nameEl.textContent = name;
      }
      current.hidden = false;
    } else if (current) {
      current.hidden = true;
    }
  }

  function requestPresign(widget, file) {
    const url = widget.dataset.presignUrl;
    const formData = new FormData();
    formData.append("app_label", widget.dataset.appLabel);
    formData.append("model_name", widget.dataset.modelName);
    formData.append("field_name", widget.dataset.fieldName);
    formData.append("filename", file.name);
    if (file.type) {
      formData.append("content_type", file.type);
    }
    if (widget.dataset.objectId) {
      formData.append("object_id", widget.dataset.objectId);
    }

    return fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(),
      },
      body: formData,
      credentials: "same-origin",
    }).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) {
          throw new Error(data.error || "Presign request failed");
        }
        return data;
      });
    });
  }

  function uploadToS3(widget, file, presign) {
    return new Promise(function (resolve, reject) {
      const formData = new FormData();
      Object.keys(presign.fields).forEach(function (key) {
        formData.append(key, presign.fields[key]);
      });
      formData.append("file", file);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", presign.url, true);

      xhr.upload.addEventListener("progress", function (event) {
        if (event.lengthComputable) {
          setProgress(widget, (event.loaded / event.total) * 100);
        }
      });

      xhr.addEventListener("load", function () {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(presign.path);
          return;
        }
        reject(new Error("S3 upload failed with status " + xhr.status));
      });

      xhr.addEventListener("error", function () {
        reject(new Error("S3 upload failed"));
      });

      xhr.send(formData);
    });
  }

  function handleFileSelected(widget, file) {
    setStatus(widget, "Requesting upload URL…", false);
    resetProgress(widget);

    requestPresign(widget, file)
      .then(function (presign) {
        setStatus(widget, "Uploading…", false);
        return uploadToS3(widget, file, presign);
      })
      .then(function (path) {
        updateCurrentFile(widget, path);
        setStatus(widget, "Upload complete.", false);
        resetProgress(widget);
        const fileInput = widget.querySelector(".s3-file-input");
        if (fileInput) {
          fileInput.value = "";
        }
      })
      .catch(function (error) {
        setStatus(widget, error.message || "Upload failed.", true);
        resetProgress(widget);
      });
  }

  function bindWidget(widget) {
    if (widget.dataset.s3FileBound === "1") {
      return;
    }
    widget.dataset.s3FileBound = "1";

    const fileInput = widget.querySelector(".s3-file-input");
    if (fileInput) {
      fileInput.addEventListener("change", function () {
        const file = fileInput.files && fileInput.files[0];
        if (file) {
          handleFileSelected(widget, file);
        }
      });
    }

    widget.addEventListener("click", function (event) {
      if (event.target.classList.contains("s3-file-clear-button")) {
        event.preventDefault();
        updateCurrentFile(widget, "");
        setStatus(widget, "File cleared.", false);
      }
    });
  }

  function init() {
    document.querySelectorAll(".s3-file-widget").forEach(bindWidget);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

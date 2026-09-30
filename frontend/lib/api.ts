export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchClient(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  options.credentials = 'include';
  
  if (!options.headers) {
    options.headers = {};
  }
  
  if (!(options.body instanceof FormData)) {
    (options.headers as any)['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, options);
  
  if (!response.ok) {
    if (response.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login';
      return new Promise(() => {}); // Prevent further execution while redirecting
    }

    let errorData;
    try {
      errorData = await response.json();
    } catch {
      throw new ApiError(response.status, "UNKNOWN_ERROR", "An unexpected error occurred");
    }
    
    throw new ApiError(
      response.status, 
      errorData?.error?.code || "UNKNOWN_ERROR", 
      errorData?.error?.message || "An unexpected error occurred"
    );
  }
  
  if (response.status === 204) {
    return null;
  }
  
  return response.json();
}

export function uploadFileWithProgress<T = any>(
  endpoint: string,
  formData: FormData,
  onProgress?: (percent: number, loaded: number, total: number) => void
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const url = `${API_BASE_URL}${endpoint}`;
    
    xhr.open("POST", url);
    xhr.withCredentials = true;

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && event.total > 0) {
          const percent = Math.min(100, Math.round((event.loaded / event.total) * 100));
          onProgress(percent, event.loaded, event.total);
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        if (xhr.status === 204) {
          resolve(null as T);
          return;
        }
        try {
          const data = JSON.parse(xhr.responseText);
          resolve(data);
        } catch {
          resolve(null as T);
        }
      } else {
        if (xhr.status === 401 && typeof window !== "undefined") {
          window.location.href = "/login";
          return;
        }

        let errorData: any = {};
        try {
          errorData = JSON.parse(xhr.responseText);
        } catch {
          // ignore json parse error
        }

        reject(
          new ApiError(
            xhr.status,
            errorData?.error?.code || "UPLOAD_FAILED",
            errorData?.error?.message || xhr.statusText || "Upload failed"
          )
        );
      }
    };

    xhr.onerror = () => {
      reject(new ApiError(0, "NETWORK_ERROR", "Network connection failed during upload"));
    };

    xhr.ontimeout = () => {
      reject(new ApiError(0, "TIMEOUT_ERROR", "Upload timed out"));
    };

    xhr.send(formData);
  });
}

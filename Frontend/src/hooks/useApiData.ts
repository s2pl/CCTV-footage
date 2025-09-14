import { useState, useEffect, useCallback } from 'react';

interface UseApiDataOptions<T> {
  initialData?: T;
  autoFetch?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  dependencies?: unknown[];
}

interface UseApiDataReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  setData: (data: T) => void;
  clearError: () => void;
}

export function useApiData<T>(
  fetchFunction: () => Promise<T>,
  options: UseApiDataOptions<T> = {}
): UseApiDataReturn<T> {
  const {
    initialData = null,
    autoFetch = true,
    onSuccess,
    onError,
    dependencies = [],
  } = options;

  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchFunction();
      setData(result);
      onSuccess?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('An error occurred');
      setError(error);
      onError?.(error);
    } finally {
      setLoading(false);
    }
  }, [fetchFunction, onSuccess, onError]);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [autoFetch, fetchData, ...dependencies]);

  return {
    data,
    loading,
    error,
    refetch,
    setData,
    clearError,
  };
}

// Specialized hooks for common use cases
export function useApiDataWithRefresh<T>(
  fetchFunction: () => Promise<T>,
  refreshInterval: number = 30000, // 30 seconds default
  options: UseApiDataOptions<T> = {}
): UseApiDataReturn<T> {
  const apiData = useApiData(fetchFunction, options);

  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(() => {
        apiData.refetch();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refreshInterval, apiData.refetch, apiData]);

  return apiData;
}

export function useApiDataWithPagination<T>(
  fetchFunction: (page: number, pageSize: number) => Promise<{ data: T[]; total: number; page: number; pageSize: number }>,
  initialPage: number = 1,
  initialPageSize: number = 10,
  options: UseApiDataOptions<{ data: T[]; total: number; page: number; pageSize: number }> = {}
) {
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const fetchWithPagination = useCallback(() => {
    return fetchFunction(page, pageSize);
  }, [fetchFunction, page, pageSize]);

  const apiData = useApiData(fetchWithPagination, {
    ...options,
    dependencies: [page, pageSize],
  });

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const changePageSize = useCallback((newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page when changing page size
  }, []);

  const nextPage = useCallback(() => {
    if (apiData.data && page < Math.ceil(apiData.data.total / pageSize)) {
      setPage(page + 1);
    }
  }, [apiData.data, page, pageSize]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(page - 1);
    }
  }, [page]);

  return {
    ...apiData,
    page,
    pageSize,
    goToPage,
    changePageSize,
    nextPage,
    prevPage,
    hasNextPage: apiData.data ? page < Math.ceil(apiData.data.total / pageSize) : false,
    hasPrevPage: page > 1,
    totalPages: apiData.data ? Math.ceil(apiData.data.total / pageSize) : 0,
  };
}

export function useApiDataWithSearch<T>(
  fetchFunction: (searchTerm: string) => Promise<T>,
  initialSearchTerm: string = '',
  debounceMs: number = 300,
  options: UseApiDataOptions<T> = {}
) {
  const [searchTerm, setSearchTerm] = useState(initialSearchTerm);
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState(initialSearchTerm);

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [searchTerm, debounceMs]);

  const fetchWithSearch = useCallback(() => {
    return fetchFunction(debouncedSearchTerm);
  }, [fetchFunction, debouncedSearchTerm]);

  const apiData = useApiData(fetchWithSearch, {
    ...options,
    autoFetch: false, // Don't auto-fetch, we'll control it
    dependencies: [debouncedSearchTerm],
  });

  // Fetch when debounced search term changes
  useEffect(() => {
    if (debouncedSearchTerm !== initialSearchTerm) {
      apiData.refetch();
    }
  }, [debouncedSearchTerm, initialSearchTerm, apiData.refetch, apiData]);

  return {
    ...apiData,
    searchTerm,
    setSearchTerm,
    debouncedSearchTerm,
  };
}

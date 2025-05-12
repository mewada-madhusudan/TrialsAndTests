#python
    
    import threading
    import concurrent.futures
    from queue import Queue
    
    # Update the LLMWorker class to handle concurrent processing
    class LLMWorker(QRunnable):
        def __init__(self, processor, data_elements, procedures, kb_name, max_concurrent=10):
            super().__init__()
            self.processor = processor
            self.data_elements = data_elements
            self.procedures = procedures
            self.kb_name = kb_name
            self.signals = WorkerSignals()
            self.max_concurrent = max_concurrent  # Maximum number of concurrent requests
    
        def run(self):
            try:
                results = []
                results_lock = threading.Lock()  # Lock for thread-safe updates to results list
                
                # Create a thread-safe queue to store the results
                result_queue = Queue()
                
                # Process queries in parallel using ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                    # Create a list to hold all futures
                    futures = []
                    
                    # Submit all tasks to the executor
                    for i in range(len(self.data_elements)):
                        future = executor.submit(
                            self._process_single_query,
                            self.data_elements[i],
                            self.procedures[i],
                            self.kb_name,
                            result_queue
                        )
                        futures.append(future)
                    
                    # Wait for all futures to complete
                    concurrent.futures.wait(futures)
                
                # Collect all results from the queue
                while not result_queue.empty():
                    results.append(result_queue.get())
                
                # Emit the results signal
                self.signals.finished.emit(results)
            except Exception as e:
                self.signals.error.emit(str(e))
        
        def _process_single_query(self, data_element, procedure, kb_name, result_queue):
            """Process a single query and put the result in the queue"""
            try:
                result = self.processor.process_query(
                    data_element,
                    procedure,
                    kb_name
                )
                
                # Add the result to the queue
                result_queue.put({
                    "data_element": data_element,
                    "procedure": procedure,
                    "kb_name": kb_name,
                    "result": result["result"],
                    "page": result["page"],
                    "conversation_id": result["conversation_id"],
                    "file": result["file"]
                })
            except Exception as e:
                print(f"Error processing query for {data_element}: {e}")
                # Add error result to queue
                result_queue.put({
                    "data_element": data_element,
                    "procedure": procedure,
                    "kb_name": kb_name,
                    "result": f"Error: {str(e)}",
                    "page": None,
                    "conversation_id": None,
                    "file": None
                })

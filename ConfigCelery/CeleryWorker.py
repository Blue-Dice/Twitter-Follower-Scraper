from celery import Celery

class CeleryWorker():
    worker_error = """
        Please specify a valid worker command.
        For more information, use "python worker.py --help"
    """
    worker_help = """
        No task routes have been defined yet.
        Please define task routes to begin the worker.
    """
    def __init__(self, broker_uri: str) -> None:
        """_summary_

        Args:
            broker_uri (str): url of the message broker
        """
        self._broker_uri = broker_uri
        self._task_routes = {}
        self._task_modules = []
        self.app = Celery(
            'Scraper',
            broker = self._broker_uri,
            backend = self._broker_uri,
        )
        
    def set_task_routes(self, routes: list[list]) -> None:
        """_summary_

        Args:
            routes (list[list]): list of ['task_name','queue_name']
        """
        self._task_routes = {}
        for route in routes:
            self._task_routes[route[0]] = {'queue':route[1]}
        self.app.conf.update({'task_routes':self._task_routes})
        self._queues = ','.join([route[1] for route in routes])
            
    def discover_tasks(self, module_locations: list[str]) -> None:
        """_summary_

        Args:
            module_locations (list[str]): list of locations of the modules of celery tasks
        """
        self._task_modules = []
        for location in module_locations:
            self._task_modules.append(location)
        self.app.autodiscover_tasks(self._task_modules,force=True)
    
    def discover_and_set_task_routes(self, routes: list[list], module_locations: list[str]) -> None:
        """_summary_

        Args:
            routes (list[list]): list of ['task_name','queue_name']
            module_locations (list[str]): list of locations of the modules of celery tasks
        """
        self.set_task_routes(routes)
        self.discover_tasks(module_locations)
        self.update_worker_help(routes, module_locations)
    
    def update_worker_help(self, routes: list[list], module_locations: list[str]) -> None:
        tasks_and_queues = ""
        task_locations = ""
        for route in routes:
            tasks_and_queues += "["+str(routes.index(route)+1)+"]"+" "+route[0]+"\t\t\t--->\t"+route[1]+"\n\t"
        for location in module_locations:
            parts = "\t--->\t".join(location.split("."))
            task_locations += "["+str(module_locations.index(location)+1)+"]"+" "+parts+"\n\t"
        self.worker_help = """
        Registered task and queues:
        {tasks_and_queues}
        Registered module locations for the above tasks:
        {task_locations}
        Worker commands:
        [1] start : to start the celery worker
        [2] purge : to purge all the tasks in the celery queues
        [3] purge -f : to purge all the tasks in the celery queues while skipping the prompt
        """.format(tasks_and_queues=tasks_and_queues, task_locations=task_locations)
    
    def define_worker_arguments(self) -> None:
        """_summary_
        
        define worker arguments for the celery worker
        """
        try:
            self.start_args = ['worker','--pool=threads','-Q',self._queues,'--loglevel=INFO']
            self.purge_args = ['purge','-Q',self._queues]
            self.force_purge_args = ['purge','-Q',self._queues,'-f']
        except Exception:
            print("Error initializing celery run arguments")
    
    def __call__(self, args):
        self.define_worker_arguments()
        try:
            if len(args) == 3 and args[1] == 'purge' and args[2] == '-f':
                self.app.start(self.force_purge_args)
            elif len(args) == 2:
                if args[1] == 'start':
                    self.app.worker_main(self.start_args)
                elif args[1] == 'purge':
                    self.app.start(self.purge_args)
                elif args[1] == '--help':
                    print(self.worker_help)
            else:
                print(self.worker_error)
        except Exception:
            print(self.worker_error)
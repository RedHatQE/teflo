from teflo.resources.actions import Action
from teflo.resources import Notification
from teflo.resources.reports import Report
from teflo.resources.executes import Execute
from teflo.resources.assets import Asset
from teflo.resources.scenario import Scenario


class ScenarioGraph():

    def __init__(self, root_scenario: Scenario = None, iterate_method: str = "by_level", scenario_vars: dict = {},
                 assets: list = [], executes: list = [],
                 reports: list = [], notifications: list = [], actions: list = [],
                 passed_tasks: list = [], failed_tasks: list = []):
        '''
        Initialization of a Sceanario Graph
        :param root_scenario: root teflo scenario object containing
        all scenario data and included scenarios
        :type root_scenario: scenario object
        :param iterate_method: iterate method for the graph traversal
        :type iterate_method: str
        '''
        self._root = root_scenario
        self._stack = []
        if iterate_method == "by_depth":
            self._stack = [root_scenario]
        elif iterate_method == "by_level":
            self._stack.append([self.root])
        else:
            raise ValueError("the iterate method value set in teflo.cfg is incorrect %s" % iterate_method)
        self._prev = None
        self._current = None
        self._visited = {}
        # There are two ways of loading resource
        # 1. by_depth
        # 2. by_level
        self._iterate_method = iterate_method
        self._assets = assets
        self._executes = executes
        self._reports = reports
        self._notifications = notifications
        self._actions = actions
        self._passed_tasks = passed_tasks
        self._failed_tasks = failed_tasks
        self._scenario_vars = scenario_vars

# root
    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, root):
        self.__init__(root, self.iterate_method)

# stack
    @property
    def stack(self):
        return self._stack

    @stack.setter
    def stack(self, stack):
        self._stack = stack

# prev
    @property
    def prev(self):
        return self._prev

    @prev.setter
    def prev(self, prev):
        self._prev = prev

# current
    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, current):
        self._current = current

# visited
    @property
    def visited(self):
        return self._visited

    @visited.setter
    def visited(self, visited):
        self._visited = visited

# iterate_method
    @property
    def iterate_method(self):
        return self._iterate_method

    @iterate_method.setter
    def iterate_method(self, value):
        raise ValueError("you cannot set iterate_method of the scenario_graph")

    # scenario_vars
    @property
    def scenario_vars(self):
        return self._scenario_vars

# iteration implemetation
    def is_visited(self, sc):
        '''
        Check if a scenario object has been visited or not
        '''
        return self.visited.get(sc, False)

    def next_unvisited_sc(self, sc_list):
        for sc in sc_list:
            if not self.is_visited(sc):
                return sc
        return None

# TODO: Scenario Graph related
# Make this to static attribute
# size
    @property
    def size(self):
        count = 0
        for sc in self:
            count += 1
        return count

    @size.setter
    def size(self, size):
        raise ValueError("you cannot set the size of the scenario_graph")

    def __len__(self):
        return self.size

    def hasChild(self, sc_list):
        '''
        Check if any scenario obejct in a list of scenarios
        contains a child
        '''
        return True in [len(sc.child_scenarios) != 0 for sc in sc_list]

    def __iter__(self):
        return self

    def __next__(self):
        '''
        The iterator method of Scenario Graph
        It is also the most important place of the ScenarioGraph Class
        It has two `iterate_method` way of traversal order

        Example:

        ->sdf0.yml
            ->sdf1.yml
                ->sdf3.yml
                ->sdf8.yml
                    ->sdf12.yml
                    ->sdf13.yml
                ->sdf5.yml
            ->sdf7.yml
                ->sdf10.yml
                ->sdf11.yml
            ->sdf2.yml
                ->sdf4.yml
                ->sdf9.yml
                ->sdf6.yml


        if iterate_method is by_depth: the traversal order will be:
            3,12,13,8,5,1,10,11,7,4,9,6,2,0
        if iterate_method is by_level: the traversal order will be:
            12,13,3,8,5,10,11,4,9,6,1,7,2,0
        '''

        if self.root is None:
            raise StopIteration

        if self.iterate_method == "by_depth":

            while len(self.stack) is not 0:
                self.current = self.stack[-1]
                if self.prev is None or self.current in self.prev.child_scenarios:

                    if self.next_unvisited_sc(self.current.child_scenarios) is not None:
                        next_sc = self.next_unvisited_sc(self.current.child_scenarios)
                        self.stack.append(next_sc)
                        self.visited[next_sc] = True
                    else:
                        self.visited[self.stack.pop()] = True
                        self.prev = self.current
                        return self.current
                elif(self.prev in self.current.child_scenarios and self.prev is not self.current.child_scenarios[-1]):
                    if self.next_unvisited_sc(self.current.child_scenarios) is not None:
                        next_sc = self.next_unvisited_sc(self.current.child_scenarios)
                        self.stack.append(next_sc)
                        self.visited[next_sc] = True
                    else:
                        self.visited[self.stack.pop()] = True
                        self.prev = self.current
                        return self.current
                else:
                    self.visited[self.stack.pop()] = True
                    self.prev = self.current
                    return self.current
                self.prev = self.current

            self.reinit()
            raise StopIteration

        elif self.iterate_method == "by_level":

            def addChildren(sc_list):
                size = len(sc_list)
                for i in range(size - 1, -1, -1):
                    sc: Scenario = sc_list[i]
                    child = sc.child_scenarios
                    if len(child) != 0:
                        self.stack.append(child)

            while len(self.stack) is not 0:
                # current scenario list
                self.current = self.stack[-1]

                # From top to down
                top_down = self.prev is not None and True in [(self.current == sc.child_scenarios) for sc in self.prev]
                if self.prev is None or top_down:
                    # current is a list of scenario
                    if self.hasChild(self.current):
                        addChildren(self.current)
                    else:
                        for sc in self.current:
                            if not self.is_visited(sc):
                                self.visited[sc] = True
                                return sc
                        self.stack.pop()
                else:
                    for sc in self.current:
                        if not self.is_visited(sc):
                            self.visited[sc] = True
                            return sc
                    self.stack.pop()

                self.prev = self.current

            self.reinit()
            raise StopIteration

    def __str__(self):
        '''
        This will return a string containing the structure of the scenario graph
        '''
        return self.root.graph_str()

    def get_assets(self):
        """
        This method returns all assests
        the current scenario graph holds
        """

        return self._assets

    def get_actions(self):
        """
        This method returns all actions
        the current scenario graph holds
        """

        return self._actions

    def get_executes(self):
        """
        This method returns all executes
        the current scenario graph holds
        """

        return self._executes

    def get_reports(self):
        """
        This method returns all reports
        the current scenario graph holds
        """

        return self._reports

    def get_passed_tasks(self):
        """
        This method returns all passed tasks
        the current scenario graph holds
        """

        return self._passed_tasks

    def get_failed_tasks(self):
        """
        This method returns all failed tasks
        the current scenario graph holds
        """

        return self._failed_tasks

    def get_notifications(self):
        """
        This method returns all notifications
        the current scenario graph holds
        """

        return self._notifications

    def add_assets(self, asset: Asset):
        """
        This method add the assest resource
        to this scenario graph
        """

        if asset not in self.get_assets():
            self._assets.append(asset)

    def add_actions(self, action: Action):
        """
        This method add the action resource
        to this scenario graph
        """

        if action not in self.get_actions():
            self._actions.append(action)

    def add_executes(self, execute: Execute):
        """
        This method add the input execute resource
        to this scenario graph
        """

        if execute not in self.get_executes():
            self._executes.append(execute)

    def add_reports(self, report: Report):
        """
        This method add all the input report
        to this scenario graph
        """

        if report not in self.get_reports():
            self._reports.append(report)

    def add_notifications(self, notification: Notification):
        """
        This method add the notification to this scenario graph
        """

        if notification not in self.get_notifications():
            self._notifications.append(notification)

    def add_tasks(self, scenario: Scenario):
        """
        This method add all tasks (failed & passed)
        to this scenario graph
        """

        if getattr(scenario, "passed_tasks", None) is not None:
            for task in scenario.passed_tasks:
                if task not in self.get_passed_tasks():
                    self._passed_tasks.append(task)
        if getattr(scenario, "failed_tasks", None) is not None:
            for task in scenario.failed_tasks:
                if task not in self.get_failed_tasks():
                    self._failed_tasks.append(task)

    def remove_resources_from_scenario(self, sc: Scenario):
        """
        This method remove all resources that the input sc has
        from the current scenario graph, it should be called right
        before the scenario will be reloaded, should be used in pair
        with `reload_resources_from_scenario`
        """

        for asset in sc.get_assets():
            self._assets.remove(asset)
        for execute in sc.get_executes():
            self._executes.remove(execute)
        for action in sc.get_actions():
            self._actions.remove(action)
        for notification in sc.get_notifications():
            self._notifications.remove(notification)
        for report in sc.get_reports():
            self._reports.remove(report)

    def reload_resources_from_scenario(self, scenario: Scenario):
        """
        This method reload the scenario graph with the input
        scenario, it should be called right after the pipeline
        run finished and scenario get reloaded, the input should
        be the reloaded scenario
        """

        self.add_tasks(scenario)
        for action in scenario.get_actions():
            self.add_actions(action)
        for asset in scenario.get_assets():
            self.add_assets(asset)
        for notification in scenario.get_notifications():
            self.add_notifications(notification)
        for report in scenario.get_reports():
            self.add_reports(report)
        for execute in scenario.get_executes():
            self.add_executes(execute)

    def get_all_resources(self):
        """
        Thie method returns all resources
        from the current scenario graph -> list
        """

        all_resources = list()

        # The order is like below so we always execute resources in below order for a single scenario node

        all_resources.extend([item for item in self.get_assets()])
        all_resources.extend([item for item in self.get_actions()])
        all_resources.extend([item for item in self.get_executes()])
        all_resources.extend([item for item in self.get_reports()])
        all_resources.extend([item for item in self.get_notifications()])
        return all_resources

    def reinit(self):
        """
        Thie method re init the whole scenario graph
        with all information the current scenario graph
        holds
        """

        self.__init__(self.root, self.iterate_method, scenario_vars=self.scenario_vars, assets=self.get_assets(),
                      executes=self.get_executes(), notifications=self.get_notifications(), reports=self.get_reports(),
                      actions=self.get_actions(), failed_tasks=self.get_failed_tasks(),
                      passed_tasks=self.get_passed_tasks())

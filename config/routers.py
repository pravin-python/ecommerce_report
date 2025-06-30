class AppRouter:
    """
    Routes read queries for specific apps to 'main'. All write operations go to 'default'.
    """
    read_only_apps = {'customer_info', 'product_tracking'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.read_only_apps:
            return 'main'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.read_only_apps:
            return None 
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.read_only_apps and
            obj2._meta.app_label in self.read_only_apps
        ):
            return True
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.read_only_apps:
            return False 
        return True 

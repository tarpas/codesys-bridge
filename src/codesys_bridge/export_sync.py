plc = [ch for ch in children if ch.get_name() == 'plc'][0]
[ch for ch in children if ch.get_name() == 'plc']
p1 = projects.create(tempfile.mktemp(), primary=True)
dev_id = device_repository.create_device_identification(4096,'101a 0750','5.1.10.10')
p1.add("plc", dev_id)

class EmptyContainer:
    def get_children(tree):              
        return []
 
def get_by_name(tree, name, raise_if_not_found=False):
    for child in tree.get_children():
        if child.get_name() == name:
            return child
    if raise_if_not_found:
        raise ValueError("Node with name {0} not found".format(name))
    return EmptyContainer()

# input is a tree and a list of names. Each item is a name one level down in the tree.
# so only 
def get_by_name_hierarchy(tree, name_hierarchy_list):
    if len(name_hierarchy_list) == 1:
        return get_by_name(tree, name_hierarchy_list[0])
    else:
        return get_by_name_hierarchy(get_by_name(tree, name_hierarchy_list[0]), name_hierarchy_list[1:])





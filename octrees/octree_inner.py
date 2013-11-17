"""
The core functionality: a purely functional implementation. We have
this two-layer setup so that octree nodes do not have to store their
own bounds.

The user should probably not ever want to import or use this code
directly.
"""

import heapq

from geometry import *



class Tree():

    def __len__(self):
        raise NotImplementedError()

    def insert(self, bounds, coords, data):
        raise NotImplementedError()

    def update(self, bounds, coords, data):
        raise NotImplementedError()

    def remove(self, bounds, coords):
        raise NotImplementedError()

    def enqueue(self, heap, bounds, pointscore, boxscore):
        raise NotImplementedError()

    def union(self, other, bounds, swapped=False):
        raise NotImplementedError()

    def rebound(self, other, bounds, swapped=False):
        raise NotImplementedError()

    def smartnode(self, data):
        if len(data) != 8:
            (((a,b),(c,d)),((e,f),(g,h))) = data
            data = [a,b,c,d,e,f,g,h]
        singleton = None
        for x in data:
            if isinstance(x,Node):
                return Node(data)
            elif isinstance(x,Singleton):
                if singleton is not None:
                    return Node(data)
                else:
                    singleton = x
        if singleton is not None:
            return singleton
        else:
            return Empty()



class Empty(Tree):

    def __init__(self):
        pass

    def __len__(self):
        return 0

    def insert(self, bounds, coords, data):
        return Singleton(coords, data)

    def update(self, bounds, coords, data):
        return Singleton(coords, data)

    def remove(self, bounds, coords):
        raise KeyError("Removing non-existent point")

    def enqueue(self, heap, bounds, pointscore, boxscore):
        pass

    def union(self, other, bounds, swapped=False):
        return other

    def rebound(self, oldbounds, newbounds):
        return self



class Singleton(Tree):

    def __init__(self, coords, data):
        self.coords = coords
        self.data = data

    def __len__(self):
        return 1

    def insert(self, bounds, coords, data):
        if self.coords == coords:
            raise KeyError("Key (%s,%s,%s) already present"%(self.coords))
        else:
            return Node().insert(bounds,self.coords,self.data).insert(bounds,coords,data)

    def update(self, bounds, coords, data):
        if self.coords == coords:
            return Singleton(coords, data)
        else:
            return Node().insert(bounds,self.coords,self.data).insert(bounds,coords,data)

    def remove(self, bounds, coords):
        if self.coords == coords:
            return Empty()
        else:
            raise KeyError("Removing non-existent point")

    def enqueue(self, heap, bounds, pointscore, boxscore):
        s = pointscore(self.coords)
        if s is not None:
            heapq.heappush(heap, (s, False, self.coords, self.data))

    def union(self, other, bounds, swapped=False):
        return other.update(bounds, self.coords, self.data)

    def rebound(self, oldbounds, newbounds):
        if point_in_box(self.coords, newbounds):
            return self
        else:
            return Empty()



class Node(Tree):

    def __init__(self, content=[Empty()]*8):
        """
        Takes either a list of eight octrees, or generators of two
        nested three deep.
        """
        if len(content)==8:
            (a,b,c,d,e,f,g,h) = content
            self.content = (((a,b),(c,d)),((e,f),(g,h)))
        else:
            self.content = tuple(tuple(tuple(b) for b in a) for a in content)

    def __len__(self):
        return sum(sum(sum(len(x) for x in b) for b in a) for a in self.content)

    def content_array(self):
        return [[list(b) for b in a] for a in self.content]

    def insert(self, bounds, coords, data):
        a = self.content_array()
        ((r,s,t),newbounds) = narrow(bounds, coords)
        a[r][s][t] = a[r][s][t].insert(newbounds, coords, data)
        return Node(a)

    def update(self, bounds, coords, data):
        a = self.content_array()
        ((r,s,t),newbounds) = narrow(bounds, coords)
        a[r][s][t] = a[r][s][t].update(newbounds, coords, data)
        return Node(a)

    def remove(self, bounds, coords):
        a = self.content_array()
        ((r,s,t),newbounds) = narrow(bounds, coords)
        a[r][s][t] = a[r][s][t].remove(newbounds, coords)
        return self.smartnode(a)

    def children_no_bounds(self):
        for u in self.content:
            for v in u:
                for w in v:
                    yield w

    def children(self, bounds):
        for (b,x) in zip(subboxes(bounds), self.children_no_bounds()):
            yield (b,x)

    def enqueue(self, heap, bounds, pointscore, boxscore):
        s = boxscore(bounds)
        if s is not None:
            heapq.heappush(heap, (s, True, bounds, self))
        
    def union(self, other, bounds, swapped=False):
        if swapped:
            return Node([x.union(y,b) for (x,y,b) in zip(self.children_no_bounds(), other.children_no_bounds(), subboxes(bounds))])
        else:
            return other.union(self, bounds, swapped=True)

    def rebound(self, oldbounds, newbounds):
        if box_contains(oldbounds, newbounds):
            return Node([self.rebound(oldbounds, b) for b in subboxes(newbounds)])
        elif boxes_disjoint(oldbounds, newbounds):
            return Empty()
        else:
            return reduce(lambda x,y:x.union(y,newbounds), (x.rebound(b,newbounds) for (b,x) in self.children(oldbounds)))

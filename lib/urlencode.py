class Urlencode():

    always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                   'abcdefghijklmnopqrstuvwxyz'
                   '0123456789' '_.-')

    def quote(self, s):
        res = []
        replacements = {}
        for c in s:
            if c in self.always_safe:
                res.append(c)
                continue
            res.append('%%%x' % ord(c))
        return ''.join(res)

    def quote_plus(self, s):
        if ' ' in s:
            s = s.replace(' ', '+')
        return self.quote(s)

    def encode(self, query):
        if isinstance(query, dict):
            query = query.items()
        l = []
        for k, v in query:
            if not isinstance(v, list):
                v = [v]
            for value in v:
                k = self.quote_plus(str(k))
                v = self.quote_plus(str(value))
                # l.append(k + '=' + v)
                l.append(v)
        return '&'.join(l)

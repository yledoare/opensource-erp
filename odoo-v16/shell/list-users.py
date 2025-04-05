for u in env['res.users'].search([]):
    print(u.login, u.name)

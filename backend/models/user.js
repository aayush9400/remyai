let users = [];

class User {
    constructor(answers) {
        this.id = users.length + 1;
        this.answers = answers;
    }

    async save() {
        users.push(this);
    }

    static async findAll() {
        return users;
    }
}

module.exports = User;

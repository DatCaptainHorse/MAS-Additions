#pragma once

#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <tuple>

namespace MASM {

	// Splits filepath to tuple of parent path and filename with extension
	std::tuple<std::string, std::string> string_split_path_file(const std::string& s)
	{
		size_t found = s.find_last_of("/\\");
		return { s.substr(0, found), s.substr(found + 1) };
	}

	// Splits string into vector of strings using char delimiter
	std::vector<std::string> string_split(const std::string& s, char delimiter)
	{
		std::vector<std::string> elems;
		std::stringstream ss(s);
		std::string item;
		while (std::getline(ss, item, delimiter))
			if (!item.empty())
				elems.emplace_back(item);

		return elems;
	}
}